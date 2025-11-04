"""
Interfaces for log sampling components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import SamplingDecision
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ISamplingEngine(ABC):
    """Interface for intelligent log sampling"""
    
    @abstractmethod
    def should_sample(self, log_level: LogLevel, logger_name: str) -> SamplingDecision:
        """Determine if a log entry should be sampled"""
        pass
    
    @abstractmethod
    def update_sampling_rates(self) -> None:
        """Update sampling rates based on current log volume"""
        pass
    
    @abstractmethod
    def get_sampling_statistics(self) -> Dict[str, Any]:
        """Get current sampling statistics and rates"""
        pass
    
    @abstractmethod
    def reset_sampling_window(self) -> None:
        """Reset the current sampling window"""
        pass
    
    @abstractmethod
    def is_sampling_active(self) -> bool:
        """Check if sampling is currently active"""
        pass