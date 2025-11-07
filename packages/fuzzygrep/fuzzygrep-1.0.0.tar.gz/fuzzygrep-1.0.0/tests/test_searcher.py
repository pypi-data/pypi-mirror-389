"""Tests for fuzzy searcher."""

import json
import tempfile
from pathlib import Path

import pytest

from fuzzygrep.core.searcher import FuzzySearcher


@pytest.fixture
def sample_data_file():
    """Create a temporary JSON file for testing."""
    data = {
        "users": [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
            {"name": "Charlie", "email": "charlie@example.com", "age": 35}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_searcher_initialization(sample_data_file):
    """Test searcher initialization."""
    searcher = FuzzySearcher(sample_data_file, use_cache=False, use_index=False)
    
    assert searcher.file_path == sample_data_file
    assert searcher.data is not None
    assert len(searcher.unique_keys) > 0


def test_key_search(sample_data_file):
    """Test searching for keys."""
    searcher = FuzzySearcher(sample_data_file, use_cache=False, use_index=False)
    
    # Search for "name"
    results = searcher.search("nam", search_type="keys", limit=5)
    
    assert len(results) > 0
    # Should find "users.name" or similar
    assert any("name" in match.lower() for match, score in results)


def test_value_search(sample_data_file):
    """Test searching for values."""
    searcher = FuzzySearcher(sample_data_file, use_cache=False, use_index=False)
    
    # Search for "Alice"
    results = searcher.search("alic", search_type="values", limit=5)
    
    assert len(results) > 0
    # Should find "Alice"
    assert any("alice" in match.lower() for match, score in results)


def test_get_values_for_key(sample_data_file):
    """Test getting values for a key."""
    searcher = FuzzySearcher(sample_data_file, use_cache=False, use_index=False)
    
    # This should return the users array
    values = searcher.get_values_for_key("users")
    assert len(values) > 0


def test_searcher_with_cache(sample_data_file):
    """Test searcher with caching enabled."""
    searcher = FuzzySearcher(sample_data_file, use_cache=True, use_index=False)
    
    # First search
    results1 = searcher.search("nam", search_type="keys", limit=5)
    
    # Second search (should hit cache)
    results2 = searcher.search("nam", search_type="keys", limit=5)
    
    assert results1 == results2


def test_searcher_with_index(sample_data_file):
    """Test searcher with indexing enabled."""
    searcher = FuzzySearcher(sample_data_file, use_cache=False, use_index=True)
    
    assert searcher.index_manager.is_indexed()
    
    results = searcher.search("nam", search_type="keys", limit=5)
    assert len(results) > 0


def test_key_filter(sample_data_file):
    """Test key filtering."""
    searcher = FuzzySearcher(sample_data_file, use_cache=False, use_index=False)
    
    # Store initial key count
    initial_key_count = len(searcher.unique_keys)
    
    # Filter to only "name" keys
    searcher.set_key_filter(["name"])
    
    # Should have fewer keys now (or equal if all keys contain "name")
    filtered_key_count = len(searcher.unique_keys)
    assert filtered_key_count <= initial_key_count
    assert all("name" in key.lower() for key in searcher.unique_keys)
    
    # Clear filter
    searcher.clear_key_filter()
    assert len(searcher.unique_keys) == initial_key_count
