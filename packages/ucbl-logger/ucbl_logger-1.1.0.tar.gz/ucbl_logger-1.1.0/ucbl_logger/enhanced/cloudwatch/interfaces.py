"""
CloudWatch Integration Interfaces

Abstract interfaces for CloudWatch integration components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import LogEntry, LogBatch, CloudWatchConfig, DeliveryStats


class ICloudWatchHandler(ABC):
    """Interface for CloudWatch log handlers."""
    
    @abstractmethod
    def send_log(self, entry: LogEntry) -> bool:
        """Send a single log entry to CloudWatch."""
        pass
    
    @abstractmethod
    def send_batch(self, batch: LogBatch) -> bool:
        """Send a batch of log entries to CloudWatch."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any pending log entries."""
        pass
    
    @abstractmethod
    def get_stats(self) -> DeliveryStats:
        """Get delivery statistics."""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the handler is healthy."""
        pass


class IBatcher(ABC):
    """Interface for intelligent log batching."""
    
    @abstractmethod
    def add_entry(self, entry: LogEntry) -> Optional[LogBatch]:
        """Add an entry to the current batch. Returns completed batch if ready."""
        pass
    
    @abstractmethod
    def get_ready_batch(self) -> Optional[LogBatch]:
        """Get a batch that's ready for delivery."""
        pass
    
    @abstractmethod
    def force_flush(self) -> Optional[LogBatch]:
        """Force flush the current batch."""
        pass
    
    @abstractmethod
    def should_create_batch(self) -> bool:
        """Check if a new batch should be created."""
        pass


class IRateLimiter(ABC):
    """Interface for CloudWatch rate limiting."""
    
    @abstractmethod
    def can_make_request(self) -> bool:
        """Check if a request can be made now."""
        pass
    
    @abstractmethod
    def record_request(self, success: bool) -> None:
        """Record a request attempt."""
        pass
    
    @abstractmethod
    def get_delay(self) -> float:
        """Get the delay before next request can be made."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset the rate limiter state."""
        pass


class ICompressor(ABC):
    """Interface for log compression."""
    
    @abstractmethod
    def compress_batch(self, batch: LogBatch) -> LogBatch:
        """Compress a log batch."""
        pass
    
    @abstractmethod
    def should_compress(self, batch: LogBatch) -> bool:
        """Check if a batch should be compressed."""
        pass
    
    @abstractmethod
    def get_compression_ratio(self) -> float:
        """Get the average compression ratio."""
        pass


class IDeduplicator(ABC):
    """Interface for log deduplication."""
    
    @abstractmethod
    def is_duplicate(self, entry: LogEntry) -> bool:
        """Check if an entry is a duplicate."""
        pass
    
    @abstractmethod
    def add_entry(self, entry: LogEntry) -> None:
        """Add an entry to the deduplication cache."""
        pass
    
    @abstractmethod
    def cleanup_old_entries(self) -> None:
        """Clean up old entries from the cache."""
        pass


class IMultiDestinationHandler(ABC):
    """Interface for multi-destination log delivery."""
    
    @abstractmethod
    def add_destination(self, destination_config: Dict[str, Any]) -> None:
        """Add a new destination."""
        pass
    
    @abstractmethod
    def remove_destination(self, destination_name: str) -> None:
        """Remove a destination."""
        pass
    
    @abstractmethod
    def send_to_all(self, batch: LogBatch) -> Dict[str, bool]:
        """Send batch to all destinations."""
        pass
    
    @abstractmethod
    def get_destination_stats(self) -> Dict[str, DeliveryStats]:
        """Get stats for all destinations."""
        pass