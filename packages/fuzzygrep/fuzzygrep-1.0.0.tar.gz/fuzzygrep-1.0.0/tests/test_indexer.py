"""Tests for trigram indexer."""

import pytest

from fuzzygrep.core.indexer import IndexManager, TrigramIndex


def test_trigram_extraction():
    """Test trigram extraction from text."""
    index = TrigramIndex()
    
    trigrams = index._get_trigrams("hello")
    assert len(trigrams) > 0
    assert "hel" in trigrams
    assert "ell" in trigrams
    assert "llo" in trigrams


def test_index_building():
    """Test building trigram index."""
    index = TrigramIndex()
    candidates = ["apple", "application", "apply", "banana", "band"]
    
    index.build(candidates)
    
    assert index.size() == len(candidates)
    assert len(index.trigram_to_indices) > 0


def test_index_search():
    """Test searching using trigram index."""
    index = TrigramIndex()
    candidates = ["apple", "application", "apply", "banana", "band"]
    
    index.build(candidates)
    
    # Search for "app"
    results = index.search("app")
    matching_candidates = index.get_candidates(results)
    
    # Should find candidates containing "app"
    assert len(matching_candidates) > 0
    assert "apple" in matching_candidates or "application" in matching_candidates


def test_index_manager():
    """Test index manager."""
    manager = IndexManager()
    
    keys = ["name", "email", "address", "phone"]
    values = ["John", "john@example.com", "123 Main St", "555-1234"]
    
    manager.build_indices(keys, values)
    
    assert manager.is_indexed()
    
    # Search keys
    key_results = manager.search_keys("nam")
    assert len(key_results) > 0
    assert "name" in key_results
    
    # Search values
    value_results = manager.search_values("joh")
    assert len(value_results) > 0


def test_index_stats():
    """Test getting index statistics."""
    manager = IndexManager()
    
    keys = ["name", "email", "address"]
    values = ["John", "john@example.com", "123 Main St"]
    
    manager.build_indices(keys, values)
    
    stats = manager.get_stats()
    
    assert stats["indexed"] is True
    assert stats["key_index"]["total_candidates"] == len(keys)
    assert stats["value_index"]["total_candidates"] == len(values)
