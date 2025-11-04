"""
Data models for log buffering
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BufferConfig:
    """Configuration for log buffering"""
    max_size: int = 10000
    flush_interval_seconds: int = 5
    max_retry_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 60.0
    failed_log_retention: int = 1000
    priority_levels: List[str] = field(default_factory=lambda: ['CRITICAL', 'ERROR'])
    enable_compression: bool = True
    batch_size: int = 100