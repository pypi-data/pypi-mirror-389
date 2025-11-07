"""Enhanced caching system for fuzzygrep with TTL and file hash invalidation."""

import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional

from cachetools import TTLCache

from fuzzygrep.utils.errors import CacheError
from fuzzygrep.utils.logging import get_logger

logger = get_logger()


class CacheManager:
    """Manages caching for search results and indices."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: int = 300,
        maxsize: int = 100,
        enabled: bool = True
    ):
        self.enabled = enabled
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'fuzzygrep'
        self.ttl = ttl
        self.maxsize = maxsize
        
        # In-memory cache for search results
        self._memory_cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        
        # File hash cache to detect changes
        self._file_hash_cache: dict[str, str] = {}
        
        # Initialize cache directory
        if self.enabled:
            self._init_cache_dir()
    
    def _init_cache_dir(self):
        """Initialize the cache directory."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Could not create cache directory: {e}")
            self.enabled = False
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of a file for cache invalidation."""
        try:
            file_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b""):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Could not compute file hash: {e}")
            return str(file_path)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get cached file hash or compute new one."""
        path_str = str(file_path)
        
        if path_str not in self._file_hash_cache:
            self._file_hash_cache[path_str] = self.compute_file_hash(file_path)
        
        return self._file_hash_cache[path_str]
    
    def invalidate_file_cache(self, file_path: Path):
        """Invalidate all cache entries for a file."""
        path_str = str(file_path)
        if path_str in self._file_hash_cache:
            del self._file_hash_cache[path_str]
        
        # Clear related disk cache
        if self.enabled:
            cache_file = self._get_cache_file_path(file_path, "index")
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    logger.debug(f"Invalidated cache: {cache_file}")
                except Exception as e:
                    logger.warning(f"Could not invalidate cache: {e}")
    
    def get_search_result(self, key: str) -> Optional[Any]:
        """Get search result from memory cache."""
        if not self.enabled:
            return None
        
        try:
            result = self._memory_cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit: {key[:50]}...")
            return result
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None
    
    def set_search_result(self, key: str, value: Any):
        """Store search result in memory cache."""
        if not self.enabled:
            return
        
        try:
            self._memory_cache[key] = value
            logger.debug(f"Cached: {key[:50]}...")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    def _get_cache_file_path(self, file_path: Path, cache_type: str) -> Path:
        """Get the cache file path for a given file and cache type."""
        file_hash = self.get_file_hash(file_path)
        cache_name = f"{file_path.stem}_{file_hash[:8]}_{cache_type}.pkl"
        return self.cache_dir / cache_name
    
    def load_index_cache(self, file_path: Path) -> Optional[Any]:
        """Load index from disk cache."""
        if not self.enabled:
            return None
        
        cache_file = self._get_cache_file_path(file_path, "index")
        
        if not cache_file.exists():
            logger.debug(f"No index cache found: {cache_file}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                index_data = pickle.load(f)
            logger.debug(f"Loaded index cache: {cache_file}")
            return index_data
        except Exception as e:
            logger.warning(f"Could not load index cache: {e}")
            # Remove corrupted cache file
            try:
                cache_file.unlink()
            except Exception:
                pass
            return None
    
    def save_index_cache(self, file_path: Path, index_data: Any):
        """Save index to disk cache."""
        if not self.enabled:
            return
        
        cache_file = self._get_cache_file_path(file_path, "index")
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(index_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(f"Saved index cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Could not save index cache: {e}")
    
    def clear_all(self):
        """Clear all caches."""
        self._memory_cache.clear()
        self._file_hash_cache.clear()
        
        if self.enabled and self.cache_dir.exists():
            try:
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                logger.info("Cleared all caches")
            except Exception as e:
                raise CacheError(f"Could not clear caches: {e}")
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        disk_cache_count = 0
        disk_cache_size = 0
        
        if self.enabled and self.cache_dir.exists():
            cache_files = list(self.cache_dir.glob("*.pkl"))
            disk_cache_count = len(cache_files)
            disk_cache_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_maxsize": self.maxsize,
            "disk_cache_count": disk_cache_count,
            "disk_cache_size_mb": disk_cache_size / (1024 * 1024),
            "ttl": self.ttl,
            "enabled": self.enabled,
        }
