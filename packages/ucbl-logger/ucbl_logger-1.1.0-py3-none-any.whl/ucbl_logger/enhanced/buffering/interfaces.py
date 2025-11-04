"""
Interfaces for log buffering components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models import EnhancedLogEntry


class IBufferManager(ABC):
    """Interface for log buffering and delivery management"""
    
    @abstractmethod
    def add_log_entry(self, log_entry: EnhancedLogEntry) -> None:
        """Add a log entry to the buffer"""
        pass
    
    @abstractmethod
    def flush_buffer(self) -> None:
        """Flush buffered logs to configured outputs"""
        pass
    
    @abstractmethod
    def handle_delivery_failure(self, log_entry: EnhancedLogEntry, error: Exception) -> None:
        """Handle failed log delivery with retry logic"""
        pass
    
    @abstractmethod
    def get_buffer_statistics(self) -> Dict[str, Any]:
        """Get buffer usage and delivery statistics"""
        pass
    
    @abstractmethod
    def is_buffer_healthy(self) -> bool:
        """Check if buffer is operating within healthy parameters"""
        pass
    
    @abstractmethod
    def clear_buffer(self) -> None:
        """Clear all buffered logs (emergency operation)"""
        pass