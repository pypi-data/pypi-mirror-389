"""Logging configuration for fuzzygrep."""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


# Global console for rich output
console = Console()


class FuzzyGrepLogger:
    """Custom logger for fuzzygrep with rich formatting."""
    
    def __init__(self, name: str = "fuzzygrep", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # Create temp log file
        self.temp_log_file = tempfile.NamedTemporaryFile(
            delete=False, mode='w', suffix='.log'
        )
        self.temp_log_path = Path(self.temp_log_file.name)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(self.temp_log_path)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        
        # Rich console handler for user-facing messages
        console_handler = RichHandler(
            console=console,
            show_time=False,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        self.verbose = False
    
    def set_verbose(self, verbose: bool):
        """Enable/disable verbose logging."""
        self.verbose = verbose
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            for handler in self.logger.handlers:
                if isinstance(handler, RichHandler):
                    handler.setLevel(logging.DEBUG)
    
    def get_log_content(self) -> str:
        """Get the content of the log file."""
        try:
            with open(self.temp_log_path, 'r') as f:
                return f.read()
        except Exception:
            return ""
    
    def cleanup(self):
        """Clean up temporary log file."""
        try:
            if self.verbose:
                console.print("\n[dim]--- Log File Content ---[/dim]")
                console.print(self.get_log_content())
                console.print("[dim]------------------------[/dim]")
            
            if self.temp_log_path.exists():
                self.temp_log_path.unlink()
        except Exception as e:
            self.logger.warning(f"Could not clean up log file: {e}")


# Global logger instance
_logger_instance: Optional[FuzzyGrepLogger] = None


def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = FuzzyGrepLogger()
    return _logger_instance.logger


def setup_logger(verbose: bool = False) -> FuzzyGrepLogger:
    """Setup and configure the global logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = FuzzyGrepLogger()
    _logger_instance.set_verbose(verbose)
    return _logger_instance


def cleanup_logger():
    """Cleanup the global logger."""
    global _logger_instance
    if _logger_instance is not None:
        _logger_instance.cleanup()
        _logger_instance = None
