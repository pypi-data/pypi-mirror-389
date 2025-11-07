"""Trigram-based indexing for fast fuzzy search."""

import re
from collections import defaultdict
from typing import Any, Optional

from fuzzygrep.utils.errors import IndexError as FuzzyIndexError
from fuzzygrep.utils.logging import get_logger

logger = get_logger()


class TrigramIndex:
    """Trigram-based index for efficient fuzzy search pre-filtering."""
    
    def __init__(self):
        # Map from trigram to set of candidate indices
        self.trigram_to_indices: dict[str, set[int]] = defaultdict(set)
        # Store original candidates
        self.candidates: list[str] = []
        # Trigram cache for candidates
        self._trigram_cache: dict[str, set[str]] = {}
    
    def build(self, candidates: list[str]):
        """Build the trigram index from a list of candidates."""
        try:
            logger.debug(f"Building index for {len(candidates)} candidates...")
            
            self.candidates = candidates
            self.trigram_to_indices.clear()
            self._trigram_cache.clear()
            
            for idx, candidate in enumerate(candidates):
                trigrams = self._get_trigrams(candidate)
                self._trigram_cache[candidate] = trigrams
                
                for trigram in trigrams:
                    self.trigram_to_indices[trigram].add(idx)
            
            logger.debug(
                f"Index built: {len(self.trigram_to_indices)} unique trigrams, "
                f"{len(self.candidates)} candidates"
            )
        except Exception as e:
            raise FuzzyIndexError(f"Failed to build index: {e}")
    
    def _get_trigrams(self, text: str) -> set[str]:
        """Extract trigrams from text."""
        # Normalize text: lowercase and remove special chars for indexing
        normalized = re.sub(r'[^a-z0-9]', '', text.lower())
        
        if len(normalized) < 3:
            # For short strings, use the string itself as a "trigram"
            return {normalized} if normalized else set()
        
        # Extract all trigrams
        trigrams = set()
        for i in range(len(normalized) - 2):
            trigrams.add(normalized[i:i+3])
        
        return trigrams
    
    def search(self, query: str, min_overlap: float = 0.2) -> list[int]:
        """
        Search the index for candidates matching the query.
        
        Returns indices of candidates that have sufficient trigram overlap.
        """
        query_trigrams = self._get_trigrams(query)
        
        if not query_trigrams:
            return list(range(len(self.candidates)))
        
        # Count trigram matches for each candidate
        candidate_scores: dict[int, int] = defaultdict(int)
        
        for trigram in query_trigrams:
            if trigram in self.trigram_to_indices:
                for idx in self.trigram_to_indices[trigram]:
                    candidate_scores[idx] += 1
        
        # Filter candidates based on minimum overlap threshold
        min_score = max(1, int(len(query_trigrams) * min_overlap))
        
        matching_indices = [
            idx for idx, score in candidate_scores.items()
            if score >= min_score
        ]
        
        logger.debug(
            f"Index search: {len(query_trigrams)} query trigrams, "
            f"{len(matching_indices)}/{len(self.candidates)} candidates match"
        )
        
        return matching_indices
    
    def get_candidates(self, indices: list[int]) -> list[str]:
        """Get candidate strings by their indices."""
        return [self.candidates[idx] for idx in indices if idx < len(self.candidates)]
    
    def size(self) -> int:
        """Get the number of indexed candidates."""
        return len(self.candidates)
    
    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        return {
            "total_candidates": len(self.candidates),
            "unique_trigrams": len(self.trigram_to_indices),
            "avg_candidates_per_trigram": (
                sum(len(indices) for indices in self.trigram_to_indices.values())
                / len(self.trigram_to_indices)
                if self.trigram_to_indices else 0
            ),
            "cache_size": len(self._trigram_cache),
        }


class IndexManager:
    """Manages indices for keys and values."""
    
    def __init__(self):
        self.key_index = TrigramIndex()
        self.value_index = TrigramIndex()
        self._indexed = False
    
    def build_indices(self, keys: list[str], values: list[str]):
        """Build indices for both keys and values."""
        logger.info("Building search indices...")
        
        try:
            self.key_index.build(keys)
            self.value_index.build(values)
            self._indexed = True
            logger.info(
                f"Indices built: {len(keys)} keys, {len(values)} values"
            )
        except Exception as e:
            logger.warning(f"Index building failed: {e}")
            self._indexed = False
    
    def search_keys(self, query: str, min_overlap: float = 0.2) -> list[str]:
        """Search keys using the index."""
        if not self._indexed:
            return []
        
        indices = self.key_index.search(query, min_overlap)
        return self.key_index.get_candidates(indices)
    
    def search_values(self, query: str, min_overlap: float = 0.2) -> list[str]:
        """Search values using the index."""
        if not self._indexed:
            return []
        
        indices = self.value_index.search(query, min_overlap)
        return self.value_index.get_candidates(indices)
    
    def is_indexed(self) -> bool:
        """Check if indices are built."""
        return self._indexed
    
    def clear(self):
        """Clear all indices."""
        self.key_index = TrigramIndex()
        self.value_index = TrigramIndex()
        self._indexed = False
        logger.debug("Indices cleared")
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all indices."""
        return {
            "indexed": self._indexed,
            "key_index": self.key_index.get_stats(),
            "value_index": self.value_index.get_stats(),
        }
