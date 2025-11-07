"""Data loaders with lazy loading and streaming support for large files."""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterator, Union

from fuzzygrep.utils.errors import (
    EmptyDataError,
    InvalidCSVError,
    InvalidJSONError,
    UnsupportedFileTypeError,
)
from fuzzygrep.utils.logging import get_logger

logger = get_logger()

# Try to import optional dependencies
try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False
    logger.debug("ijson not available, streaming JSON disabled")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    logger.debug("pandas not available, CSV chunking disabled")


class DataLoader:
    """Base class for data loaders."""
    
    SUPPORTED_FORMATS = ['.json', '.csv']
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._validate_file()
    
    def _validate_file(self):
        """Validate that the file exists and is supported."""
        if not self.file_path.exists():
            from fuzzygrep.utils.errors import FileNotFoundError
            raise FileNotFoundError(str(self.file_path))
        
        if self.file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise UnsupportedFileTypeError(
                str(self.file_path),
                self.SUPPORTED_FORMATS
            )
    
    def load(self) -> Any:
        """Load the entire file into memory."""
        ext = self.file_path.suffix.lower()
        if ext == '.json':
            return self._load_json()
        elif ext == '.csv':
            return self._load_csv()
    
    def stream(self, chunk_size: int = 1000) -> Iterator[Any]:
        """Stream the file in chunks for memory efficiency."""
        ext = self.file_path.suffix.lower()
        if ext == '.json':
            yield from self._stream_json()
        elif ext == '.csv':
            yield from self._stream_csv(chunk_size)
    
    def _load_json(self) -> Any:
        """Load entire JSON file into memory."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                raise EmptyDataError(str(self.file_path))
            
            return data
        except json.JSONDecodeError as e:
            raise InvalidJSONError(str(self.file_path), str(e))
        except Exception as e:
            raise InvalidJSONError(str(self.file_path), str(e))
    
    def _stream_json(self) -> Iterator[dict]:
        """Stream JSON file using ijson for large files."""
        if not HAS_IJSON:
            # Fallback to loading entire file
            data = self._load_json()
            if isinstance(data, list):
                yield from data
            else:
                yield data
            return
        
        try:
            with open(self.file_path, 'rb') as f:
                # Try to parse as array of objects
                try:
                    parser = ijson.items(f, 'item')
                    for item in parser:
                        yield item
                except (ijson.JSONError, ijson.IncompleteJSONError):
                    # Not an array, load as single object
                    f.seek(0)
                    data = json.load(f)
                    yield data
        except Exception as e:
            raise InvalidJSONError(str(self.file_path), str(e))
    
    def _load_csv(self) -> list[dict]:
        """Load entire CSV file into memory."""
        try:
            with open(self.file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            if not data:
                raise EmptyDataError(str(self.file_path))
            
            return data
        except Exception as e:
            raise InvalidCSVError(str(self.file_path), str(e))
    
    def _stream_csv(self, chunk_size: int = 1000) -> Iterator[list[dict]]:
        """Stream CSV file in chunks."""
        if HAS_PANDAS:
            # Use pandas for efficient chunking
            try:
                chunks = pd.read_csv(
                    self.file_path,
                    chunksize=chunk_size,
                    encoding='utf-8'
                )
                for chunk in chunks:
                    yield chunk.to_dict('records')
            except Exception as e:
                raise InvalidCSVError(str(self.file_path), str(e))
        else:
            # Fallback to manual chunking
            try:
                with open(self.file_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    chunk = []
                    for row in reader:
                        chunk.append(row)
                        if len(chunk) >= chunk_size:
                            yield chunk
                            chunk = []
                    if chunk:
                        yield chunk
            except Exception as e:
                raise InvalidCSVError(str(self.file_path), str(e))
    
    def get_file_size(self) -> int:
        """Get file size in bytes."""
        return self.file_path.stat().st_size
    
    def should_use_streaming(self, threshold_mb: int = 10) -> bool:
        """Determine if streaming should be used based on file size."""
        size_mb = self.get_file_size() / (1024 * 1024)
        return size_mb > threshold_mb


class KeyValueExtractor:
    """Extract keys and values from structured data."""
    
    @staticmethod
    def extract_keys(data: Any, prefix: str = "") -> list[str]:
        """Recursively extract all keys from nested data structures."""
        keys = []
        
        if isinstance(data, dict):
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.append(full_key)
                keys.extend(KeyValueExtractor.extract_keys(v, full_key))
        elif isinstance(data, list):
            for item in data:
                keys.extend(KeyValueExtractor.extract_keys(item, prefix))
        
        return keys
    
    @staticmethod
    def extract_values(data: Any) -> list[str]:
        """Recursively extract all values from nested data structures."""
        values = []
        
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, (dict, list)):
                    values.extend(KeyValueExtractor.extract_values(v))
                else:
                    values.append(str(v))
        elif isinstance(data, list):
            for item in data:
                values.extend(KeyValueExtractor.extract_values(item))
        
        return values
    
    @staticmethod
    def get_value_by_path(data: Any, path: str) -> list[Any]:
        """Retrieve all values for a given path from nested data."""
        values = []
        
        if isinstance(data, list):
            for item in data:
                values.extend(KeyValueExtractor.get_value_by_path(item, path))
            return values
        
        keys = path.split('.')
        value = data
        
        for key in keys:
            try:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return []
            except (KeyError, TypeError, IndexError):
                return []
        
        return [value]
    
    @staticmethod
    def build_value_to_key_map(data: Any, prefix: str = "") -> dict[str, set[str]]:
        """Build a map from values to the keys that contain them."""
        value_to_keys = {}
        
        if isinstance(data, dict):
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                
                if isinstance(v, (dict, list)):
                    nested_map = KeyValueExtractor.build_value_to_key_map(v, full_key)
                    for val, keys in nested_map.items():
                        if val not in value_to_keys:
                            value_to_keys[val] = set()
                        value_to_keys[val].update(keys)
                else:
                    val_str = str(v)
                    if val_str not in value_to_keys:
                        value_to_keys[val_str] = set()
                    value_to_keys[val_str].add(full_key)
        
        elif isinstance(data, list):
            for item in data:
                nested_map = KeyValueExtractor.build_value_to_key_map(item, prefix)
                for val, keys in nested_map.items():
                    if val not in value_to_keys:
                        value_to_keys[val] = set()
                    value_to_keys[val].update(keys)
        
        return value_to_keys
    
    @staticmethod
    def optimize_memory(values: list[str]) -> list[str]:
        """Optimize memory usage through string interning and deduplication."""
        # String interning for common values
        interned = [sys.intern(v) for v in values]
        
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for v in interned:
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        
        original_count = len(values)
        if original_count > len(deduped):
            reduction = 100 - (len(deduped) / original_count * 100)
            logger.debug(
                f"Memory optimization: {original_count} -> {len(deduped)} "
                f"unique values ({reduction:.1f}% reduction)"
            )
        
        return deduped
