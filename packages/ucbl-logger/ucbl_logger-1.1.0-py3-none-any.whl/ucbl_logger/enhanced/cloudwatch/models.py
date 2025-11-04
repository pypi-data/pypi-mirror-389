"""
CloudWatch Integration Models

Data models for CloudWatch integration including configuration, batching, and compression.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time


class CompressionType(Enum):
    """Supported compression types for CloudWatch logs."""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"


class BackoffStrategy(Enum):
    """Backoff strategies for rate limiting."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class CloudWatchConfig:
    """Configuration for CloudWatch integration."""
    
    # Basic CloudWatch settings
    region: str = "us-east-1"
    log_group_name: Optional[str] = None
    log_stream_name: Optional[str] = None
    auto_create_group: bool = True
    auto_create_stream: bool = True
    
    # Batching configuration
    batch_size: int = 100
    batch_timeout: float = 5.0  # seconds
    max_batch_size: int = 1000
    
    # Rate limiting
    max_requests_per_second: float = 5.0
    burst_capacity: int = 10
    
    # Compression
    compression_type: CompressionType = CompressionType.GZIP
    compression_threshold: int = 1024  # bytes
    
    # Retry configuration
    max_retries: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    
    # Cost optimization
    enable_deduplication: bool = True
    deduplication_window: int = 300  # seconds
    
    # Tagging
    default_tags: Dict[str, str] = field(default_factory=dict)
    
    # Multi-destination support
    enable_parallel_delivery: bool = False
    failover_destinations: List[str] = field(default_factory=list)


@dataclass
class BatchConfig:
    """Configuration for intelligent batching."""
    
    target_batch_size: int = 100
    max_batch_size: int = 1000
    min_batch_size: int = 10
    batch_timeout: float = 5.0
    adaptive_sizing: bool = True
    size_adjustment_factor: float = 0.1


@dataclass
class CompressionConfig:
    """Configuration for log compression."""
    
    compression_type: CompressionType = CompressionType.GZIP
    compression_level: int = 6
    threshold_bytes: int = 1024
    enable_deduplication: bool = True


@dataclass
class LogEntry:
    """Individual log entry for CloudWatch."""
    
    timestamp: int
    message: str
    log_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_cloudwatch_event(self) -> Dict[str, Any]:
        """Convert to CloudWatch log event format."""
        return {
            'timestamp': self.timestamp,
            'message': self.message
        }


@dataclass
class LogBatch:
    """Batch of log entries for CloudWatch delivery."""
    
    entries: List[LogEntry] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    compressed: bool = False
    compressed_size: Optional[int] = None
    original_size: Optional[int] = None
    
    def add_entry(self, entry: LogEntry) -> None:
        """Add a log entry to the batch."""
        self.entries.append(entry)
    
    def size(self) -> int:
        """Get the number of entries in the batch."""
        return len(self.entries)
    
    def is_empty(self) -> bool:
        """Check if the batch is empty."""
        return len(self.entries) == 0
    
    def get_size_bytes(self) -> int:
        """Calculate the total size of the batch in bytes."""
        if self.compressed and self.compressed_size:
            return self.compressed_size
        
        total_size = 0
        for entry in self.entries:
            total_size += len(entry.message.encode('utf-8'))
        return total_size
    
    def to_cloudwatch_events(self) -> List[Dict[str, Any]]:
        """Convert batch to CloudWatch log events format."""
        return [entry.to_cloudwatch_event() for entry in self.entries]


@dataclass
class RateLimitState:
    """State for rate limiting tracking."""
    
    requests_made: int = 0
    window_start: float = field(default_factory=time.time)
    last_request_time: float = 0.0
    backoff_until: float = 0.0
    consecutive_failures: int = 0


@dataclass
class DeliveryStats:
    """Statistics for CloudWatch delivery."""
    
    total_batches_sent: int = 0
    total_entries_sent: int = 0
    total_bytes_sent: int = 0
    total_compressed_bytes: int = 0
    total_failures: int = 0
    total_retries: int = 0
    average_batch_size: float = 0.0
    compression_ratio: float = 0.0
    last_delivery_time: Optional[float] = None
    
    def update_delivery(self, batch: LogBatch, success: bool) -> None:
        """Update stats after a delivery attempt."""
        if success:
            self.total_batches_sent += 1
            self.total_entries_sent += batch.size()
            self.total_bytes_sent += batch.get_size_bytes()
            if batch.compressed and batch.compressed_size:
                self.total_compressed_bytes += batch.compressed_size
            self.last_delivery_time = time.time()
            
            # Update average batch size
            if self.total_batches_sent > 0:
                self.average_batch_size = self.total_entries_sent / self.total_batches_sent
            
            # Update compression ratio
            if self.total_bytes_sent > 0 and self.total_compressed_bytes > 0:
                self.compression_ratio = self.total_compressed_bytes / self.total_bytes_sent
        else:
            self.total_failures += 1


@dataclass
class CloudWatchDestination:
    """Configuration for a CloudWatch destination."""
    
    name: str
    region: str
    log_group: str
    log_stream: str
    config: CloudWatchConfig
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True