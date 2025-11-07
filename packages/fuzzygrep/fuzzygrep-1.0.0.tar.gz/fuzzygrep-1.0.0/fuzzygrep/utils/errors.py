"""Custom exception hierarchy for fuzzygrep."""

from typing import Optional


class FuzzyGrepError(Exception):
    """Base exception for all fuzzygrep errors."""
    
    def __init__(self, message: str, suggestion: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\n💡 Suggestion: {self.suggestion}"
        return self.message


class FileNotFoundError(FuzzyGrepError):
    """Raised when a file cannot be found."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"File not found: '{file_path}'",
            "Check that the file path is correct and the file exists."
        )


class UnsupportedFileTypeError(FuzzyGrepError):
    """Raised when an unsupported file type is encountered."""
    
    def __init__(self, file_path: str, supported_types: list[str]):
        super().__init__(
            f"Unsupported file type for '{file_path}'",
            f"Supported file types: {', '.join(supported_types)}"
        )


class InvalidJSONError(FuzzyGrepError):
    """Raised when JSON parsing fails."""
    
    def __init__(self, file_path: str, error: str):
        super().__init__(
            f"Invalid JSON in '{file_path}': {error}",
            "Validate your JSON file using a JSON validator (e.g., jsonlint)."
        )


class InvalidCSVError(FuzzyGrepError):
    """Raised when CSV parsing fails."""
    
    def __init__(self, file_path: str, error: str):
        super().__init__(
            f"Invalid CSV in '{file_path}': {error}",
            "Check that the file is properly formatted with consistent delimiters."
        )


class EmptyDataError(FuzzyGrepError):
    """Raised when a file contains no data."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"File '{file_path}' contains no data",
            "Ensure the file has valid content."
        )


class IndexError(FuzzyGrepError):
    """Raised when indexing operations fail."""
    
    def __init__(self, message: str):
        super().__init__(
            f"Index error: {message}",
            "Try rebuilding the index or check available disk space."
        )


class CacheError(FuzzyGrepError):
    """Raised when cache operations fail."""
    
    def __init__(self, message: str):
        super().__init__(
            f"Cache error: {message}",
            "Try clearing the cache or check file permissions."
        )


class ConfigurationError(FuzzyGrepError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str):
        super().__init__(
            f"Configuration error: {message}",
            "Check your configuration file syntax and values."
        )
