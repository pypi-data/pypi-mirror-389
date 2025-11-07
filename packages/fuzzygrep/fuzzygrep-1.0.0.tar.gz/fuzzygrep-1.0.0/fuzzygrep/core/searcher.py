"""Enhanced fuzzy search with parallel processing and indexing."""

import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from rapidfuzz import fuzz, process

from fuzzygrep.core.cache import CacheManager
from fuzzygrep.core.indexer import IndexManager
from fuzzygrep.core.loaders import DataLoader, KeyValueExtractor
from fuzzygrep.utils.logging import get_logger

logger = get_logger()


class FuzzySearcher:
    """
    Enhanced fuzzy searcher with indexing, caching, and parallel processing.
    """
    
    def __init__(
        self,
        file_path: Path,
        use_cache: bool = True,
        use_index: bool = True,
        cache_ttl: int = 300,
        parallel: bool = True,
        max_workers: Optional[int] = None
    ):
        self.file_path = file_path
        self.use_cache = use_cache
        self.use_index = use_index
        self.parallel = parallel
        self.max_workers = max_workers or min(4, (os.cpu_count() or 1))
        
        # Initialize components
        self.loader = DataLoader(file_path)
        self.cache = CacheManager(ttl=cache_ttl, enabled=use_cache)
        self.index_manager = IndexManager()
        
        # Data structures
        self.data: Any = None
        self.unique_keys: list[str] = []
        self.unique_values: list[str] = []
        self.value_to_keys_map: dict[str, list[str]] = {}
        
        # Key filtering
        self._allowed_keys_filter: list[str] = []
        
        # Load and process data
        self._load_and_process()
    
    def _load_and_process(self):
        """Load data and build indices."""
        logger.info(f"Loading {self.file_path.name}...")
        
        # Check if we should use streaming
        if self.loader.should_use_streaming():
            logger.info("Large file detected, using streaming mode...")
            self._load_streaming()
        else:
            self._load_full()
        
        # Build indices
        if self.use_index and self.unique_keys and self.unique_values:
            # Try to load from cache
            cached_index = self.cache.load_index_cache(self.file_path)
            if cached_index:
                logger.info("Loaded index from cache")
                self.unique_keys = cached_index['keys']
                self.unique_values = cached_index['values']
                self.value_to_keys_map = cached_index['value_to_keys_map']
                self.index_manager.build_indices(self.unique_keys, self.unique_values)
            else:
                self.index_manager.build_indices(self.unique_keys, self.unique_values)
                # Save index to cache
                self.cache.save_index_cache(self.file_path, {
                    'keys': self.unique_keys,
                    'values': self.unique_values,
                    'value_to_keys_map': self.value_to_keys_map,
                })
        
        logger.info(
            f"Loaded {len(self.unique_keys)} keys, {len(self.unique_values)} values"
        )
    
    def _load_full(self):
        """Load entire file into memory."""
        self.data = self.loader.load()
        
        # Extract keys and values
        if self.parallel and len(str(self.data)) > 100000:
            # Use parallel processing for large datasets
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                key_future = executor.submit(KeyValueExtractor.extract_keys, self.data)
                value_future = executor.submit(KeyValueExtractor.extract_values, self.data)
                map_future = executor.submit(
                    KeyValueExtractor.build_value_to_key_map, self.data
                )
                
                all_keys = key_future.result()
                all_values = value_future.result()
                value_to_keys_map_raw = map_future.result()
        else:
            # Sequential processing for small datasets
            all_keys = KeyValueExtractor.extract_keys(self.data)
            all_values = KeyValueExtractor.extract_values(self.data)
            value_to_keys_map_raw = KeyValueExtractor.build_value_to_key_map(self.data)
        
        # Optimize memory
        all_values = KeyValueExtractor.optimize_memory(all_values)
        
        # Store processed data
        self.unique_keys = sorted(list(set(all_keys)))
        self.unique_values = sorted(list(set(all_values)))
        self.value_to_keys_map = {
            val: sorted(list(keys)) for val, keys in value_to_keys_map_raw.items()
        }
    
    def _load_streaming(self):
        """Load data using streaming for large files."""
        all_keys = []
        all_values = []
        value_to_keys_map_raw = {}
        
        for chunk in self.loader.stream():
            if isinstance(chunk, list):
                for item in chunk:
                    all_keys.extend(KeyValueExtractor.extract_keys(item))
                    all_values.extend(KeyValueExtractor.extract_values(item))
                    
                    chunk_map = KeyValueExtractor.build_value_to_key_map(item)
                    for val, keys in chunk_map.items():
                        if val not in value_to_keys_map_raw:
                            value_to_keys_map_raw[val] = set()
                        value_to_keys_map_raw[val].update(keys)
            else:
                all_keys.extend(KeyValueExtractor.extract_keys(chunk))
                all_values.extend(KeyValueExtractor.extract_values(chunk))
                
                chunk_map = KeyValueExtractor.build_value_to_key_map(chunk)
                for val, keys in chunk_map.items():
                    if val not in value_to_keys_map_raw:
                        value_to_keys_map_raw[val] = set()
                    value_to_keys_map_raw[val].update(keys)
        
        # Store the last chunk as data for value retrieval
        self.data = self.loader.load()
        
        # Optimize memory
        all_values = KeyValueExtractor.optimize_memory(all_values)
        
        # Store processed data
        self.unique_keys = sorted(list(set(all_keys)))
        self.unique_values = sorted(list(set(all_values)))
        self.value_to_keys_map = {
            val: sorted(list(keys)) for val, keys in value_to_keys_map_raw.items()
        }
    
    def search(
        self,
        query: str,
        search_type: str = "keys",
        limit: int = 10,
        score_cutoff: int = 60
    ) -> list[tuple[str, float]]:
        """
        Perform fuzzy search.
        
        Args:
            query: Search query
            search_type: "keys" or "values"
            limit: Maximum number of results
            score_cutoff: Minimum score threshold (0-100)
        
        Returns:
            List of (match, score) tuples
        """
        # Check cache
        if self.use_cache:
            file_hash = self.cache.get_file_hash(self.file_path)
            cache_key = f"{query}:{limit}:{search_type}:{score_cutoff}:{file_hash}"
            cached_result = self.cache.get_search_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Get candidates
        if search_type == "keys":
            candidates = self.unique_keys
        else:
            candidates = self.unique_values
        
        # Use index to pre-filter candidates if available
        if self.use_index and self.index_manager.is_indexed():
            if search_type == "keys":
                indexed_candidates = self.index_manager.search_keys(query)
            else:
                indexed_candidates = self.index_manager.search_values(query)
            
            # Use indexed candidates if they significantly reduce the search space
            if indexed_candidates and len(indexed_candidates) < len(candidates) * 0.5:
                candidates = indexed_candidates
                logger.debug(
                    f"Index reduced search space: "
                    f"{len(candidates)} candidates (from original)"
                )
        
        # Choose scorer based on dataset size
        if len(candidates) > 10000:
            scorer = fuzz.ratio  # Faster for large datasets
            logger.debug(f"Using fast scorer for {len(candidates)} candidates")
        else:
            scorer = fuzz.WRatio  # More accurate for smaller datasets
        
        # Perform fuzzy search
        matches = process.extract(
            query,
            candidates,
            scorer=scorer,
            limit=limit,
            score_cutoff=score_cutoff
        )
        
        # Clean results
        results = [(m[0], m[1]) for m in matches]
        
        # Cache results
        if self.use_cache:
            self.cache.set_search_result(cache_key, results)
        
        return results
    
    def get_values_for_key(self, key: str) -> list[Any]:
        """Get all values for a given key path."""
        if not self.data:
            return []
        return KeyValueExtractor.get_value_by_path(self.data, key)
    
    def get_keys_for_value(self, value: str) -> list[str]:
        """Get all keys that contain a given value."""
        return self.value_to_keys_map.get(value, [])
    
    def set_key_filter(self, patterns: list[str]):
        """Filter keys by patterns."""
        self._allowed_keys_filter = patterns
        self._apply_key_filter()
    
    def clear_key_filter(self):
        """Clear key filtering."""
        self._allowed_keys_filter = []
        self._apply_key_filter()
    
    def _apply_key_filter(self):
        """Apply key filtering and rebuild indices."""
        if not self._allowed_keys_filter:
            # No filter, reload everything
            self._load_and_process()
            return
        
        # Filter keys
        all_keys = KeyValueExtractor.extract_keys(self.data)
        filtered_keys = []
        
        for key in all_keys:
            for pattern in self._allowed_keys_filter:
                if pattern.lower() in key.lower():
                    filtered_keys.append(key)
                    break
        
        self.unique_keys = sorted(list(set(filtered_keys)))
        
        # Rebuild value map for filtered keys
        filtered_value_to_keys = {}
        for val, keys in self.value_to_keys_map.items():
            filtered_associated_keys = [k for k in keys if k in self.unique_keys]
            if filtered_associated_keys:
                filtered_value_to_keys[val] = filtered_associated_keys
        
        self.value_to_keys_map = filtered_value_to_keys
        self.unique_values = sorted(list(filtered_value_to_keys.keys()))
        
        # Rebuild indices
        if self.use_index:
            self.index_manager.build_indices(self.unique_keys, self.unique_values)
        
        logger.info(
            f"Filter applied: {len(self.unique_keys)} keys, "
            f"{len(self.unique_values)} values"
        )
    
    def reload(self):
        """Reload data from file."""
        logger.info("Reloading data...")
        self.cache.invalidate_file_cache(self.file_path)
        self._load_and_process()
    
    def get_stats(self) -> dict[str, Any]:
        """Get searcher statistics."""
        return {
            "file_path": str(self.file_path),
            "file_size_mb": self.loader.get_file_size() / (1024 * 1024),
            "total_keys": len(self.unique_keys),
            "total_values": len(self.unique_values),
            "key_filter_active": bool(self._allowed_keys_filter),
            "cache_enabled": self.use_cache,
            "index_enabled": self.use_index,
            "parallel_enabled": self.parallel,
            "cache_stats": self.cache.get_cache_stats(),
            "index_stats": self.index_manager.get_stats(),
        }
