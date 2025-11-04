"""
Advanced sampling engine with volume-based and adaptive strategies
"""

import time
import random
import math
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional
from .interfaces import ISamplingEngine, LogLevel
from .models import SamplingDecision, SamplingConfig, VolumeWindow, SamplingStatistics, SamplingStrategy
from .dynamic_adjuster import DynamicRateAdjuster


class AdvancedSamplingEngine(ISamplingEngine):
    """Advanced sampling engine with volume-based and adaptive strategies"""
    
    def __init__(self, config: SamplingConfig):
        self.config = config
        self.statistics = SamplingStatistics()
        
        # Sliding window for volume tracking
        self.volume_windows: deque[VolumeWindow] = deque(maxlen=config.sliding_window_segments)
        self._initialize_windows()
        
        # Adaptive sampling state
        self.historical_volumes: deque[int] = deque(maxlen=config.adaptive_history_size)
        self.current_adaptive_rate = config.default_rate
        
        # Per-level counters for current window
        self.current_window_counters = defaultdict(int)
        self.last_window_reset = time.time()
        
        # Rate adjustment tracking
        self.last_rate_adjustment = time.time()
        self.consecutive_adjustments = 0
        
        # Dynamic rate adjuster for ML-inspired algorithms
        self.dynamic_adjuster = DynamicRateAdjuster(config)
        
    def _initialize_windows(self) -> None:
        """Initialize sliding window segments"""
        current_time = time.time()
        segment_size = self.config.get_window_segment_size()
        
        for i in range(self.config.sliding_window_segments):
            window_time = current_time - (i * segment_size)
            self.volume_windows.appendleft(VolumeWindow(timestamp=window_time, count=0))
    
    def should_sample(self, log_level: LogLevel, logger_name: str) -> SamplingDecision:
        """Determine if a log entry should be sampled using advanced strategies"""
        self.statistics.total_logs += 1
        self._update_level_statistics(log_level.value, 'total')
        
        # Always sample if sampling is disabled or in debug mode
        if not self.config.enabled or self.config.debug_mode:
            decision = SamplingDecision(
                should_sample=True,
                sampling_rate=1.0,
                reason="sampling_disabled",
                metadata={"debug_mode": self.config.debug_mode}
            )
            self._record_sampling_decision(decision, log_level.value)
            return decision
        
        # Priority handling - always preserve critical logs
        if self._should_preserve_by_priority(log_level):
            decision = SamplingDecision(
                should_sample=True,
                sampling_rate=1.0,
                reason="priority_preservation",
                metadata={"log_level": log_level.value}
            )
            self._record_sampling_decision(decision, log_level.value)
            return decision
        
        # Update volume tracking
        self._update_volume_tracking()
        
        # Determine sampling rate based on strategy
        sampling_rate = self._calculate_sampling_rate(log_level)
        
        # Make sampling decision
        should_sample = random.random() < sampling_rate
        
        # Create decision with comprehensive metadata
        decision = SamplingDecision(
            should_sample=should_sample,
            sampling_rate=sampling_rate,
            reason=self._get_sampling_reason(),
            metadata=self._get_sampling_metadata(log_level)
        )
        
        self._record_sampling_decision(decision, log_level.value)
        return decision
    
    def _should_preserve_by_priority(self, log_level: LogLevel) -> bool:
        """Check if log should be preserved based on priority rules"""
        if self.config.preserve_errors and log_level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return True
        if self.config.preserve_warnings and log_level == LogLevel.WARNING:
            return True
        return False
    
    def _update_volume_tracking(self) -> None:
        """Update sliding window volume tracking"""
        current_time = time.time()
        segment_size = self.config.get_window_segment_size()
        
        # Check if we need to advance to a new window segment
        if self.volume_windows:
            latest_window = self.volume_windows[-1]
            if current_time - latest_window.timestamp >= segment_size:
                # Add new window segment
                new_window = VolumeWindow(timestamp=current_time, count=1)
                self.volume_windows.append(new_window)
            else:
                # Increment current window
                latest_window.count += 1
        
        # Update current window counters
        self.current_window_counters['total'] += 1
    
    def _calculate_sampling_rate(self, log_level: LogLevel) -> float:
        """Calculate sampling rate based on configured strategy"""
        if self.config.strategy == SamplingStrategy.LEVEL_BASED:
            return self.config.get_rate_for_level(log_level.value)
        
        elif self.config.strategy == SamplingStrategy.VOLUME_BASED:
            return self._calculate_volume_based_rate(log_level)
        
        elif self.config.strategy == SamplingStrategy.ADAPTIVE:
            return self._calculate_adaptive_rate(log_level)
        
        else:  # DISABLED
            return 1.0
    
    def _calculate_volume_based_rate(self, log_level: LogLevel) -> float:
        """Calculate sampling rate based on current log volume"""
        current_volume = self._get_current_window_volume()
        base_rate = self.config.get_rate_for_level(log_level.value)
        
        if current_volume <= self.config.volume_threshold:
            # Low volume - use base rate
            return base_rate
        
        elif current_volume <= self.config.high_volume_threshold:
            # Medium volume - linear reduction
            volume_ratio = (current_volume - self.config.volume_threshold) / \
                          (self.config.high_volume_threshold - self.config.volume_threshold)
            reduction_factor = 1.0 - (volume_ratio * 0.7)  # Reduce up to 70%
            return max(base_rate * reduction_factor, self.config.adaptive_min_rate)
        
        else:
            # High volume - aggressive sampling
            return max(base_rate * 0.1, self.config.adaptive_min_rate)
    
    def _calculate_adaptive_rate(self, log_level: LogLevel) -> float:
        """Calculate adaptive sampling rate using ML-inspired algorithms"""
        if not self.config.adaptive_enabled:
            return self.config.get_rate_for_level(log_level.value)
        
        current_volume = self._get_current_window_volume()
        
        # Check if dynamic adjustment is needed
        if self.dynamic_adjuster.should_adjust_rate(current_volume, self.current_adaptive_rate):
            # Use ML-inspired dynamic adjustment
            new_rate = self.dynamic_adjuster.calculate_new_rate(
                current_volume, self.current_adaptive_rate, log_level.value
            )
            self.current_adaptive_rate = new_rate
            return new_rate
        
        # Fallback to traditional adaptive calculation
        base_rate = self.config.get_rate_for_level(log_level.value)
        
        # Calculate trend from historical data
        trend_factor = self._calculate_volume_trend()
        
        # Adjust rate based on current volume and trend
        if current_volume > self.config.volume_threshold:
            # High volume detected
            if self.config.volume_threshold == 0:
                volume_pressure = 10.0
            else:
                volume_pressure = min(current_volume / self.config.volume_threshold, 10.0)
            rate_reduction = math.log(volume_pressure) * self.config.adaptive_adjustment_factor
            
            # Apply trend factor
            if trend_factor > 1.0:  # Volume increasing
                rate_reduction *= trend_factor
            
            adjusted_rate = base_rate * (1.0 - rate_reduction)
        else:
            # Normal volume - potentially increase rate if trend is decreasing
            if trend_factor < 1.0 and self.current_adaptive_rate < base_rate:
                recovery_factor = (1.0 - trend_factor) * self.config.adaptive_adjustment_factor
                adjusted_rate = min(self.current_adaptive_rate * (1.0 + recovery_factor), base_rate)
            else:
                adjusted_rate = base_rate
        
        # Clamp to configured bounds
        adjusted_rate = max(min(adjusted_rate, self.config.adaptive_max_rate), 
                           self.config.adaptive_min_rate)
        
        self.current_adaptive_rate = adjusted_rate
        return adjusted_rate
    
    def _calculate_volume_trend(self) -> float:
        """Calculate volume trend factor from historical data"""
        if len(self.historical_volumes) < 2:
            return 1.0
        
        # Calculate simple moving average trend
        recent_avg = sum(list(self.historical_volumes)[-3:]) / min(3, len(self.historical_volumes))
        older_avg = sum(list(self.historical_volumes)[:-3]) / max(1, len(self.historical_volumes) - 3)
        
        if older_avg == 0:
            return 1.0
        
        return recent_avg / older_avg
    
    def _get_current_window_volume(self) -> int:
        """Get total volume for current sliding window"""
        return sum(window.count for window in self.volume_windows)
    
    def _get_sampling_reason(self) -> str:
        """Get reason for current sampling decision"""
        if self.config.strategy == SamplingStrategy.VOLUME_BASED:
            volume = self._get_current_window_volume()
            if volume > self.config.high_volume_threshold:
                return "high_volume_aggressive_sampling"
            elif volume > self.config.volume_threshold:
                return "medium_volume_sampling"
            else:
                return "low_volume_normal_sampling"
        
        elif self.config.strategy == SamplingStrategy.ADAPTIVE:
            return "adaptive_sampling"
        
        else:
            return "level_based_sampling"
    
    def _get_sampling_metadata(self, log_level: LogLevel) -> Dict[str, Any]:
        """Get comprehensive metadata for sampling decision"""
        base_metadata = {
            "strategy": self.config.strategy.value,
            "log_level": log_level.value,
            "current_volume": self._get_current_window_volume(),
            "volume_threshold": self.config.volume_threshold,
            "adaptive_rate": self.current_adaptive_rate,
            "window_segments": len(self.volume_windows),
            "total_logs_processed": self.statistics.total_logs,
            "sampling_efficiency": self._calculate_sampling_efficiency()
        }
        
        # Add dynamic adjustment metadata if adaptive sampling is enabled
        if self.config.adaptive_enabled:
            adjustment_metadata = self.dynamic_adjuster.get_adjustment_metadata()
            base_metadata.update({
                "dynamic_adjustment": adjustment_metadata,
                "ml_patterns_detected": len(adjustment_metadata.get('detected_patterns', [])),
                "adjustment_effectiveness": adjustment_metadata.get('average_effectiveness', 0.0)
            })
        
        return base_metadata
    
    def _calculate_sampling_efficiency(self) -> float:
        """Calculate current sampling efficiency (sampled/total)"""
        if self.statistics.total_logs == 0:
            return 1.0
        return self.statistics.sampled_logs / self.statistics.total_logs
    
    def _record_sampling_decision(self, decision: SamplingDecision, log_level: str) -> None:
        """Record sampling decision in statistics"""
        if decision.should_sample:
            self.statistics.sampled_logs += 1
            self._update_level_statistics(log_level, 'sampled')
        else:
            self.statistics.dropped_logs += 1
            self._update_level_statistics(log_level, 'dropped')
        
        self.statistics.current_rate = decision.sampling_rate
    
    def _update_level_statistics(self, log_level: str, stat_type: str) -> None:
        """Update per-level statistics"""
        if log_level not in self.statistics.level_statistics:
            self.statistics.level_statistics[log_level] = {
                'total': 0, 'sampled': 0, 'dropped': 0
            }
        
        self.statistics.level_statistics[log_level][stat_type] += 1
    
    def update_sampling_rates(self) -> None:
        """Update sampling rates based on current log volume and trends"""
        current_time = time.time()
        
        # Check if we should update historical volumes
        if current_time - self.last_window_reset >= self.config.window_size_seconds:
            current_volume = self._get_current_window_volume()
            self.historical_volumes.append(current_volume)
            
            # Reset current window counters
            self.current_window_counters.clear()
            self.last_window_reset = current_time
            
            # Update statistics
            self.statistics.window_volume = current_volume
            
            # Trigger adaptive adjustment if needed
            if self.config.adaptive_enabled:
                self._perform_adaptive_adjustment()
    
    def _perform_adaptive_adjustment(self) -> None:
        """Perform adaptive rate adjustment based on recent patterns"""
        if len(self.historical_volumes) < 2:
            return
        
        current_time = time.time()
        if current_time - self.last_rate_adjustment < 30:  # Minimum 30 seconds between adjustments
            return
        
        # Analyze recent volume patterns
        recent_volume = self.historical_volumes[-1]
        avg_volume = sum(self.historical_volumes) / len(self.historical_volumes)
        
        # Determine if adjustment is needed
        if recent_volume > avg_volume * 1.5:  # 50% above average
            self.consecutive_adjustments += 1
        elif recent_volume < avg_volume * 0.7:  # 30% below average
            self.consecutive_adjustments = max(0, self.consecutive_adjustments - 1)
        
        self.statistics.adaptive_adjustments += 1
        self.last_rate_adjustment = current_time
    
    def get_sampling_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sampling statistics and rates"""
        base_stats = {
            'enabled': self.config.enabled,
            'strategy': self.config.strategy.value,
            'current_adaptive_rate': self.current_adaptive_rate,
            'current_window_volume': self._get_current_window_volume(),
            'volume_threshold': self.config.volume_threshold,
            'statistics': {
                'total_logs': self.statistics.total_logs,
                'sampled_logs': self.statistics.sampled_logs,
                'dropped_logs': self.statistics.dropped_logs,
                'sampling_efficiency': self._calculate_sampling_efficiency(),
                'adaptive_adjustments': self.statistics.adaptive_adjustments,
                'level_statistics': dict(self.statistics.level_statistics)
            },
            'volume_windows': [
                {'timestamp': w.timestamp, 'count': w.count} 
                for w in self.volume_windows
            ],
            'historical_volumes': list(self.historical_volumes),
            'trend_factor': self._calculate_volume_trend()
        }
        
        # Add dynamic adjustment statistics
        if self.config.adaptive_enabled:
            base_stats['dynamic_adjustment'] = self.dynamic_adjuster.get_adjustment_metadata()
        
        return base_stats
    
    def reset_sampling_window(self) -> None:
        """Reset the current sampling window and statistics"""
        self.volume_windows.clear()
        self._initialize_windows()
        self.current_window_counters.clear()
        self.historical_volumes.clear()
        self.statistics = SamplingStatistics()
        self.current_adaptive_rate = self.config.default_rate
        self.last_window_reset = time.time()
        self.last_rate_adjustment = time.time()
        self.consecutive_adjustments = 0
        
        # Reset dynamic adjuster state
        self.dynamic_adjuster.reset_learning_state()
    
    def is_sampling_active(self) -> bool:
        """Check if sampling is currently active"""
        return (self.config.enabled and 
                not self.config.debug_mode and 
                self._get_current_window_volume() > 0)
    
    def enable_debug_mode(self) -> None:
        """Enable debug mode to disable sampling temporarily"""
        self.config.debug_mode = True
    
    def disable_debug_mode(self) -> None:
        """Disable debug mode to re-enable sampling"""
        self.config.debug_mode = False
    
    def get_current_sampling_rate(self, log_level: LogLevel) -> float:
        """Get current sampling rate for a specific log level"""
        if not self.config.enabled or self.config.debug_mode:
            return 1.0
        
        if self._should_preserve_by_priority(log_level):
            return 1.0
        
        return self._calculate_sampling_rate(log_level)