"""
Base implementation for log sampling components
"""

import time
import random
from collections import defaultdict
from typing import Dict, Any
from .interfaces import ISamplingEngine, LogLevel
from .models import SamplingDecision, SamplingConfig


class BaseSamplingEngine(ISamplingEngine):
    """Base implementation of sampling engine"""
    
    def __init__(self, config: SamplingConfig):
        self.config = config
        self.log_counters = defaultdict(int)
        self.window_start = time.time()
        self.current_rates = {}
    
    def should_sample(self, log_level: LogLevel, logger_name: str) -> SamplingDecision:
        """Determine if a log entry should be sampled"""
        if not self.config.enabled or self.config.debug_mode:
            return SamplingDecision(
                should_sample=True,
                sampling_rate=1.0,
                reason="sampling_disabled"
            )
        
        # Always preserve errors if configured
        if self.config.preserve_errors and log_level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return SamplingDecision(
                should_sample=True,
                sampling_rate=1.0,
                reason="preserve_errors"
            )
        
        # Get sampling rate for this level
        rate = self.config.get_rate_for_level(log_level.value)
        should_sample = random.random() < rate
        
        return SamplingDecision(
            should_sample=should_sample,
            sampling_rate=rate,
            reason="level_based_sampling"
        )
    
    def update_sampling_rates(self) -> None:
        """Update sampling rates based on current log volume"""
        current_time = time.time()
        if current_time - self.window_start >= self.config.window_size_seconds:
            # Reset window
            self.log_counters.clear()
            self.window_start = current_time
    
    def get_sampling_statistics(self) -> Dict[str, Any]:
        """Get current sampling statistics and rates"""
        return {
            'enabled': self.config.enabled,
            'current_rates': self.current_rates,
            'log_counters': dict(self.log_counters),
            'window_start': self.window_start
        }
    
    def reset_sampling_window(self) -> None:
        """Reset the current sampling window"""
        self.log_counters.clear()
        self.window_start = time.time()
    
    def is_sampling_active(self) -> bool:
        """Check if sampling is currently active"""
        return self.config.enabled and not self.config.debug_mode