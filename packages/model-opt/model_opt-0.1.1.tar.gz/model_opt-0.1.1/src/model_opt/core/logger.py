"""Structured logging with different verbosity levels."""
import logging
import sys
from pathlib import Path
from typing import Optional


class StructuredLogger:
    """Structured logger with file and console handlers."""
    
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    
    def __init__(
        self,
        name: str = 'model_opt',
        level: str = 'INFO',
        log_file: Optional[str] = None
    ):
        """Initialize structured logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional path to log file
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)
    
    def set_level(self, level: str):
        """Set logging level.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(log_level)


# Global logger instance
_logger_instance: Optional[StructuredLogger] = None


def get_logger(
    name: str = 'model_opt',
    level: str = 'INFO',
    log_file: Optional[str] = None
) -> StructuredLogger:
    """Get or create global logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional path to log file
        
    Returns:
        StructuredLogger instance
    """
    global _logger_instance
    if _logger_instance is None or log_file is not None:
        _logger_instance = StructuredLogger(name, level, log_file)
    return _logger_instance


def set_log_file(log_file: str):
    """Set log file for global logger.
    
    Args:
        log_file: Path to log file
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(log_file=log_file)
    else:
        # Recreate logger with new file
        level = logging.getLevelName(_logger_instance.logger.level)
        _logger_instance = StructuredLogger(
            name=_logger_instance.logger.name,
            level=level,
            log_file=log_file
        )

