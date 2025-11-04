"""
Data models for log sampling
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum
import time


class SamplingStrategy(Enum):
    """Sampling strategy enumeration"""
    VOLUME_BASED = "volume_based"
    LEVEL_BASED = "level_based"
    ADAPTIVE = "adaptive"
    DISABLED = "disabled"


@dataclass
class SamplingDecision:
    """Result of sampling decision"""
    should_sample: bool
    sampling_rate: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VolumeWindow:
    """Sliding window for volume tracking"""
    timestamp: float
    count: int
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


@dataclass
class SamplingStatistics:
    """Comprehensive sampling statistics"""
    total_logs: int = 0
    sampled_logs: int = 0
    dropped_logs: int = 0
    current_rate: float = 1.0
    window_volume: int = 0
    adaptive_adjustments: int = 0
    last_adjustment_time: float = field(default_factory=time.time)
    level_statistics: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class SamplingConfig:
    """Configuration for log sampling"""
    enabled: bool = True
    strategy: SamplingStrategy = SamplingStrategy.ADAPTIVE
    default_rate: float = 1.0
    level_rates: Dict[str, float] = field(default_factory=lambda: {
        'DEBUG': 0.1,
        'INFO': 0.5,
        'WARNING': 0.8,
        'ERROR': 1.0,
        'CRITICAL': 1.0
    })
    
    # Volume-based sampling configuration
    volume_threshold: int = 1000  # logs per minute
    high_volume_threshold: int = 5000  # logs per minute for aggressive sampling
    window_size_seconds: int = 60
    sliding_window_segments: int = 6  # Number of segments in sliding window
    
    # Adaptive sampling configuration
    adaptive_enabled: bool = True
    adaptive_min_rate: float = 0.01  # Minimum sampling rate (1%)
    adaptive_max_rate: float = 1.0   # Maximum sampling rate (100%)
    adaptive_adjustment_factor: float = 0.1  # How aggressively to adjust rates
    adaptive_history_size: int = 10  # Number of historical windows to consider
    
    # Priority handling
    preserve_errors: bool = True
    preserve_warnings: bool = False
    debug_mode: bool = False
    
    def get_rate_for_level(self, level: str) -> float:
        """Get sampling rate for specific log level"""
        return self.level_rates.get(level.upper(), self.default_rate)
    
    def get_window_segment_size(self) -> float:
        """Get the size of each sliding window segment in seconds"""
        if self.sliding_window_segments == 0:
            return self.window_size_seconds
        return self.window_size_seconds / self.sliding_window_segments