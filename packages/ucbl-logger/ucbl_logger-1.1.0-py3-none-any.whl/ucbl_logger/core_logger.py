import logging
from typing import Dict, Any, Optional
from .interfaces import ILogger, LogLevel

class CoreLogger(ILogger):
    """Core logging implementation - Single Responsibility"""
    
    def __init__(self, logger_name: str = __name__, log_level: LogLevel = LogLevel.INFO):
        self._logger = logging.getLogger(logger_name)
        self._setup_logger(log_level)
    
    def _setup_logger(self, log_level: LogLevel) -> None:
        """Setup the underlying logger with handler and formatter"""
        level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        self._logger.setLevel(level_mapping[log_level])
        
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level_mapping[log_level])
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def log(self, level: LogLevel, message: str) -> None:
        """Log a message at the specified level"""
        level_mapping = {
            LogLevel.DEBUG: self._logger.debug,
            LogLevel.INFO: self._logger.info,
            LogLevel.WARNING: self._logger.warning,
            LogLevel.ERROR: self._logger.error,
            LogLevel.CRITICAL: self._logger.critical
        }
        
        log_func = level_mapping.get(level, self._logger.info)
        log_func(message)
    
    def set_level(self, level: LogLevel) -> None:
        """Change the logging level"""
        level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        self._logger.setLevel(level_mapping[level])
        for handler in self._logger.handlers:
            handler.setLevel(level_mapping[level])