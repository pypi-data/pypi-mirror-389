"""Tests for data loaders."""

import json
import tempfile
from pathlib import Path

import pytest

from fuzzygrep.core.loaders import DataLoader, KeyValueExtractor
from fuzzygrep.utils.errors import EmptyDataError, InvalidJSONError, UnsupportedFileTypeError


@pytest.fixture
def sample_json_file():
    """Create a temporary JSON file for testing."""
    data = {
        "name": "John Doe",
        "age": 30,
        "address": {
            "street": "123 Main St",
            "city": "New York"
        },
        "hobbies": ["reading", "cycling"]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age,city\n")
        f.write("John,30,New York\n")
        f.write("Jane,25,Los Angeles\n")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_loader_json(sample_json_file):
    """Test loading JSON file."""
    loader = DataLoader(sample_json_file)
    data = loader.load()
    
    assert data is not None
    assert data["name"] == "John Doe"
    assert data["age"] == 30


def test_loader_csv(sample_csv_file):
    """Test loading CSV file."""
    loader = DataLoader(sample_csv_file)
    data = loader.load()
    
    assert data is not None
    assert len(data) == 2
    assert data[0]["name"] == "John"


def test_loader_unsupported_file():
    """Test loading unsupported file type."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(UnsupportedFileTypeError):
            DataLoader(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_key_extractor(sample_json_file):
    """Test key extraction."""
    loader = DataLoader(sample_json_file)
    data = loader.load()
    
    keys = KeyValueExtractor.extract_keys(data)
    
    assert "name" in keys
    assert "age" in keys
    assert "address" in keys
    assert "address.street" in keys
    assert "address.city" in keys


def test_value_extractor(sample_json_file):
    """Test value extraction."""
    loader = DataLoader(sample_json_file)
    data = loader.load()
    
    values = KeyValueExtractor.extract_values(data)
    
    assert "John Doe" in values
    assert "30" in values
    assert "123 Main St" in values


def test_value_to_key_map(sample_json_file):
    """Test value to key mapping."""
    loader = DataLoader(sample_json_file)
    data = loader.load()
    
    value_map = KeyValueExtractor.build_value_to_key_map(data)
    
    assert "John Doe" in value_map
    assert "name" in value_map["John Doe"]


def test_memory_optimization():
    """Test memory optimization."""
    values = ["test", "test", "foo", "bar", "test", "foo"]
    optimized = KeyValueExtractor.optimize_memory(values)
    
    # Should deduplicate while preserving order
    assert len(optimized) == 3
    assert optimized == ["test", "foo", "bar"]
