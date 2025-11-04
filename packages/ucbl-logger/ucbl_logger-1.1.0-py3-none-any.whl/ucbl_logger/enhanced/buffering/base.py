"""
Base implementation for log buffering components
"""

import time
from collections import deque
from typing import Dict, Any
from .interfaces import IBufferManager
from ..models import EnhancedLogEntry
from .models import BufferConfig


class BaseBufferManager(IBufferManager):
    """Base implementation of buffer manager"""
    
    def __init__(self, config: BufferConfig):
        self.config = config
        self.buffer = deque(maxlen=config.max_size)
        self.failed_logs = deque(maxlen=config.failed_log_retention)
        self.stats = {
            'total_logs': 0,
            'dropped_logs': 0,
            'failed_deliveries': 0,
            'successful_deliveries': 0
        }
    
    def add_log_entry(self, log_entry: EnhancedLogEntry) -> None:
        """Add a log entry to the buffer"""
        self.buffer.append(log_entry)
        self.stats['total_logs'] += 1
    
    def flush_buffer(self) -> None:
        """Flush buffered logs to configured outputs"""
        # Basic implementation - will be enhanced with actual output handling
        while self.buffer:
            log_entry = self.buffer.popleft()
            try:
                # Simulate successful delivery
                self.stats['successful_deliveries'] += 1
            except Exception as e:
                self.handle_delivery_failure(log_entry, e)
    
    def handle_delivery_failure(self, log_entry: EnhancedLogEntry, error: Exception) -> None:
        """Handle failed log delivery with retry logic"""
        self.failed_logs.append((log_entry, error, time.time()))
        self.stats['failed_deliveries'] += 1
    
    def get_buffer_statistics(self) -> Dict[str, Any]:
        """Get buffer usage and delivery statistics"""
        return {
            'buffer_size': len(self.buffer),
            'max_buffer_size': self.config.max_size,
            'failed_logs_count': len(self.failed_logs),
            'stats': self.stats.copy()
        }
    
    def is_buffer_healthy(self) -> bool:
        """Check if buffer is operating within healthy parameters"""
        buffer_usage = len(self.buffer) / self.config.max_size
        return buffer_usage < 0.8  # Consider healthy if less than 80% full
    
    def clear_buffer(self) -> None:
        """Clear all buffered logs (emergency operation)"""
        dropped_count = len(self.buffer)
        self.buffer.clear()
        self.stats['dropped_logs'] += dropped_count