"""
Dynamic sampling rate adjustment algorithms with ML-inspired approaches
"""

import time
import math
from collections import deque
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from .models import SamplingConfig


@dataclass
class VolumePattern:
    """Represents a detected volume pattern"""
    pattern_type: str  # 'spike', 'sustained_high', 'gradual_increase', 'normal', 'decreasing'
    confidence: float  # 0.0 to 1.0
    predicted_duration: Optional[float] = None  # seconds
    recommended_rate: Optional[float] = None


@dataclass
class AdjustmentHistory:
    """History of rate adjustments for learning"""
    timestamp: float
    old_rate: float
    new_rate: float
    trigger_volume: int
    effectiveness_score: Optional[float] = None  # Calculated later


class DynamicRateAdjuster:
    """
    Dynamic sampling rate adjuster with ML-inspired algorithms
    """
    
    def __init__(self, config: SamplingConfig):
        self.config = config
        
        # Sliding window for sophisticated volume analysis
        self.volume_history: deque[Tuple[float, int]] = deque(maxlen=100)  # (timestamp, volume)
        self.rate_history: deque[AdjustmentHistory] = deque(maxlen=50)
        
        # Pattern detection state
        self.detected_patterns: List[VolumePattern] = []
        self.pattern_confidence_threshold = 0.7
        
        # Learning parameters
        self.learning_rate = 0.1
        self.momentum = 0.9
        self.previous_gradient = 0.0
        
        # Adaptive thresholds
        self.dynamic_thresholds = {
            'low': config.volume_threshold * 0.5,
            'medium': config.volume_threshold,
            'high': config.volume_threshold * 2.0,
            'critical': config.volume_threshold * 5.0
        }
        
        # Rate adjustment constraints
        self.max_adjustment_per_window = 0.3  # Maximum 30% change per adjustment
        self.min_adjustment_interval = 30.0   # Minimum 30 seconds between adjustments
        self.last_adjustment_time = 0.0
        
        # Effectiveness tracking
        self.adjustment_effectiveness = deque(maxlen=20)
        
    def should_adjust_rate(self, current_volume: int, current_rate: float) -> bool:
        """Determine if rate adjustment is needed"""
        current_time = time.time()
        
        # Check minimum interval
        if current_time - self.last_adjustment_time < self.min_adjustment_interval:
            return False
        
        # Update volume history
        self.volume_history.append((current_time, current_volume))
        
        # Detect patterns and determine if adjustment is needed
        patterns = self._detect_volume_patterns()
        
        if not patterns:
            return False
        
        # Check if any high-confidence pattern suggests adjustment
        for pattern in patterns:
            if (pattern.confidence > self.pattern_confidence_threshold and 
                pattern.recommended_rate and 
                abs(pattern.recommended_rate - current_rate) > 0.1):
                return True
        
        return False
    
    def calculate_new_rate(self, current_volume: int, current_rate: float, 
                          log_level: str) -> float:
        """Calculate new sampling rate using ML-inspired algorithms"""
        
        # Get base rate for the log level
        base_rate = self.config.get_rate_for_level(log_level)
        
        # Detect current patterns
        patterns = self._detect_volume_patterns()
        
        if not patterns:
            return self._calculate_gradient_based_rate(current_volume, current_rate, base_rate)
        
        # Use pattern-based adjustment
        primary_pattern = max(patterns, key=lambda p: p.confidence)
        
        if primary_pattern.recommended_rate:
            new_rate = primary_pattern.recommended_rate
        else:
            new_rate = self._calculate_pattern_adjusted_rate(
                primary_pattern, current_volume, current_rate, base_rate
            )
        
        # Apply learning-based refinement
        new_rate = self._apply_learning_refinement(new_rate, current_rate, current_volume)
        
        # Constrain the adjustment
        new_rate = self._constrain_rate_adjustment(current_rate, new_rate)
        
        # Record the adjustment
        self._record_adjustment(current_rate, new_rate, current_volume)
        
        return new_rate
    
    def _detect_volume_patterns(self) -> List[VolumePattern]:
        """Detect volume patterns using sliding window analysis"""
        if len(self.volume_history) < 5:
            return []
        
        patterns = []
        recent_volumes = [vol for _, vol in list(self.volume_history)[-10:]]
        
        # Detect spike pattern
        spike_pattern = self._detect_spike_pattern(recent_volumes)
        if spike_pattern:
            patterns.append(spike_pattern)
        
        # Detect sustained high volume
        sustained_pattern = self._detect_sustained_high_pattern(recent_volumes)
        if sustained_pattern:
            patterns.append(sustained_pattern)
        
        # Detect gradual increase/decrease
        trend_pattern = self._detect_trend_pattern(recent_volumes)
        if trend_pattern:
            patterns.append(trend_pattern)
        
        # Detect periodic patterns
        periodic_pattern = self._detect_periodic_pattern()
        if periodic_pattern:
            patterns.append(periodic_pattern)
        
        self.detected_patterns = patterns
        return patterns
    
    def _detect_spike_pattern(self, volumes: List[int]) -> Optional[VolumePattern]:
        """Detect sudden volume spikes"""
        if len(volumes) < 3:
            return None
        
        recent_avg = sum(volumes[-3:]) / 3
        baseline_avg = sum(volumes[:-3]) / max(1, len(volumes) - 3)
        
        if baseline_avg == 0:
            return None
        
        spike_ratio = recent_avg / baseline_avg
        
        if spike_ratio > 3.0:  # 3x increase
            confidence = min(0.9, (spike_ratio - 3.0) / 7.0 + 0.7)  # Scale confidence
            recommended_rate = max(0.1, 1.0 / math.sqrt(spike_ratio))
            
            return VolumePattern(
                pattern_type='spike',
                confidence=confidence,
                predicted_duration=60.0,  # Assume spikes last ~1 minute
                recommended_rate=recommended_rate
            )
        
        return None
    
    def _detect_sustained_high_pattern(self, volumes: List[int]) -> Optional[VolumePattern]:
        """Detect sustained high volume periods"""
        if len(volumes) < 5:
            return None
        
        high_threshold = self.dynamic_thresholds['high']
        high_count = sum(1 for vol in volumes[-5:] if vol > high_threshold)
        
        if high_count >= 4:  # 4 out of 5 recent windows are high
            avg_volume = sum(volumes[-5:]) / 5
            confidence = min(0.95, high_count / 5.0)
            
            # Calculate rate based on sustained volume level
            volume_pressure = avg_volume / high_threshold
            recommended_rate = max(0.05, 1.0 / volume_pressure)
            
            return VolumePattern(
                pattern_type='sustained_high',
                confidence=confidence,
                predicted_duration=300.0,  # Assume sustained patterns last ~5 minutes
                recommended_rate=recommended_rate
            )
        
        return None
    
    def _detect_trend_pattern(self, volumes: List[int]) -> Optional[VolumePattern]:
        """Detect gradual increasing or decreasing trends"""
        if len(volumes) < 6:
            return None
        
        # Calculate linear regression slope
        n = len(volumes)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(volumes)
        sum_xy = sum(x * y for x, y in zip(x_values, volumes))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend strength
        avg_volume = sum_y / n
        relative_slope = abs(slope) / max(1, avg_volume)
        
        if relative_slope > 0.1:  # Significant trend
            if slope > 0:
                pattern_type = 'gradual_increase'
                # Preemptively reduce rate for increasing trend
                trend_factor = min(3.0, 1.0 + relative_slope * 2)
                recommended_rate = max(0.1, 1.0 / trend_factor)
            else:
                pattern_type = 'decreasing'
                # Gradually increase rate for decreasing trend
                recovery_factor = min(2.0, 1.0 + abs(relative_slope))
                recommended_rate = min(1.0, 0.5 * recovery_factor)
            
            confidence = min(0.8, relative_slope * 2)
            
            return VolumePattern(
                pattern_type=pattern_type,
                confidence=confidence,
                predicted_duration=180.0,  # Trends typically last ~3 minutes
                recommended_rate=recommended_rate
            )
        
        return None
    
    def _detect_periodic_pattern(self) -> Optional[VolumePattern]:
        """Detect periodic volume patterns (basic implementation)"""
        if len(self.volume_history) < 20:
            return None
        
        # Simple periodic detection - look for repeating high/low cycles
        volumes = [vol for _, vol in list(self.volume_history)[-20:]]
        
        # Check for alternating high/low pattern
        high_threshold = self.dynamic_thresholds['medium']
        pattern_matches = 0
        
        for i in range(2, len(volumes) - 2, 2):
            if (volumes[i] > high_threshold and volumes[i-1] < high_threshold and 
                volumes[i+1] < high_threshold):
                pattern_matches += 1
        
        if pattern_matches >= 3:  # At least 3 cycles detected
            confidence = min(0.7, pattern_matches / 5.0)
            return VolumePattern(
                pattern_type='periodic',
                confidence=confidence,
                predicted_duration=120.0,
                recommended_rate=0.7  # Moderate sampling for periodic patterns
            )
        
        return None
    
    def _calculate_gradient_based_rate(self, current_volume: int, current_rate: float, 
                                     base_rate: float) -> float:
        """Calculate rate using gradient descent-inspired approach"""
        
        # Calculate "loss" - how far we are from optimal volume
        target_volume = self.dynamic_thresholds['medium']
        volume_error = (current_volume - target_volume) / target_volume
        
        # Calculate gradient (how much to adjust rate)
        gradient = volume_error * self.learning_rate
        
        # Apply momentum
        gradient_with_momentum = gradient + self.momentum * self.previous_gradient
        self.previous_gradient = gradient_with_momentum
        
        # Calculate new rate
        new_rate = current_rate - gradient_with_momentum
        
        # Ensure we don't deviate too far from base rate
        max_deviation = base_rate * 0.8
        new_rate = max(base_rate - max_deviation, min(base_rate + max_deviation, new_rate))
        
        return new_rate
    
    def _calculate_pattern_adjusted_rate(self, pattern: VolumePattern, current_volume: int,
                                       current_rate: float, base_rate: float) -> float:
        """Calculate rate adjustment based on detected pattern"""
        
        if pattern.recommended_rate:
            # Use pattern's recommended rate as starting point
            new_rate = pattern.recommended_rate
        else:
            # Calculate based on pattern type
            if pattern.pattern_type == 'spike':
                volume_multiplier = current_volume / self.dynamic_thresholds['medium']
                new_rate = base_rate / max(1.0, math.sqrt(volume_multiplier))
            
            elif pattern.pattern_type == 'sustained_high':
                pressure_factor = current_volume / self.dynamic_thresholds['high']
                new_rate = base_rate / max(1.0, pressure_factor)
            
            elif pattern.pattern_type == 'gradual_increase':
                # Preemptive reduction
                new_rate = current_rate * 0.8
            
            elif pattern.pattern_type == 'decreasing':
                # Gradual recovery
                new_rate = min(base_rate, current_rate * 1.2)
            
            else:  # periodic or unknown
                new_rate = current_rate
        
        # Weight by pattern confidence
        confidence_weighted_rate = (pattern.confidence * new_rate + 
                                  (1 - pattern.confidence) * current_rate)
        
        return confidence_weighted_rate
    
    def _apply_learning_refinement(self, proposed_rate: float, current_rate: float,
                                 current_volume: int) -> float:
        """Apply learning-based refinement using historical effectiveness"""
        
        if not self.adjustment_effectiveness:
            return proposed_rate
        
        # Calculate average effectiveness of recent adjustments
        avg_effectiveness = sum(self.adjustment_effectiveness) / len(self.adjustment_effectiveness)
        
        # If recent adjustments have been ineffective, be more conservative
        if avg_effectiveness < 0.3:
            conservative_factor = 0.5
            refined_rate = current_rate + conservative_factor * (proposed_rate - current_rate)
        else:
            # If adjustments have been effective, be more aggressive
            aggressive_factor = min(1.5, avg_effectiveness * 2)
            refined_rate = current_rate + aggressive_factor * (proposed_rate - current_rate)
        
        return refined_rate
    
    def _constrain_rate_adjustment(self, current_rate: float, new_rate: float) -> float:
        """Apply constraints to rate adjustment"""
        
        # Limit maximum change per adjustment
        max_change = current_rate * self.max_adjustment_per_window
        if new_rate > current_rate + max_change:
            new_rate = current_rate + max_change
        elif new_rate < current_rate - max_change:
            new_rate = current_rate - max_change
        
        # Ensure rate stays within global bounds
        new_rate = max(self.config.adaptive_min_rate, 
                      min(self.config.adaptive_max_rate, new_rate))
        
        return new_rate
    
    def _record_adjustment(self, old_rate: float, new_rate: float, trigger_volume: int) -> None:
        """Record rate adjustment for learning purposes"""
        
        adjustment = AdjustmentHistory(
            timestamp=time.time(),
            old_rate=old_rate,
            new_rate=new_rate,
            trigger_volume=trigger_volume
        )
        
        self.rate_history.append(adjustment)
        self.last_adjustment_time = adjustment.timestamp
        
        # Calculate effectiveness of previous adjustment if possible
        if len(self.rate_history) >= 2:
            self._calculate_adjustment_effectiveness()
    
    def _calculate_adjustment_effectiveness(self) -> None:
        """Calculate effectiveness of recent rate adjustments"""
        
        if len(self.rate_history) < 2 or len(self.volume_history) < 10:
            return
        
        # Get the previous adjustment
        prev_adjustment = self.rate_history[-2]
        current_adjustment = self.rate_history[-1]
        
        # Find volume data around the previous adjustment
        adjustment_time = prev_adjustment.timestamp
        
        # Get volumes before and after the adjustment
        before_volumes = []
        after_volumes = []
        
        for timestamp, volume in self.volume_history:
            if timestamp < adjustment_time:
                before_volumes.append(volume)
            elif timestamp > adjustment_time:
                after_volumes.append(volume)
        
        if len(before_volumes) < 3 or len(after_volumes) < 3:
            return
        
        # Calculate effectiveness based on volume reduction
        before_avg = sum(before_volumes[-3:]) / 3
        after_avg = sum(after_volumes[:3]) / 3
        
        if before_avg > 0:
            volume_reduction = (before_avg - after_avg) / before_avg
            
            # Rate reduction should correlate with volume reduction
            rate_reduction = (prev_adjustment.old_rate - prev_adjustment.new_rate) / prev_adjustment.old_rate
            
            if rate_reduction > 0:  # We reduced the rate
                effectiveness = max(0.0, min(1.0, volume_reduction / rate_reduction))
            else:  # We increased the rate
                effectiveness = max(0.0, min(1.0, -volume_reduction / abs(rate_reduction)))
            
            prev_adjustment.effectiveness_score = effectiveness
            self.adjustment_effectiveness.append(effectiveness)
    
    def get_adjustment_metadata(self) -> Dict[str, Any]:
        """Get comprehensive metadata about rate adjustments"""
        
        recent_patterns = [
            {
                'type': p.pattern_type,
                'confidence': p.confidence,
                'recommended_rate': p.recommended_rate,
                'predicted_duration': p.predicted_duration
            }
            for p in self.detected_patterns
        ]
        
        recent_adjustments = [
            {
                'timestamp': adj.timestamp,
                'old_rate': adj.old_rate,
                'new_rate': adj.new_rate,
                'trigger_volume': adj.trigger_volume,
                'effectiveness': adj.effectiveness_score
            }
            for adj in list(self.rate_history)[-5:]  # Last 5 adjustments
        ]
        
        return {
            'dynamic_thresholds': self.dynamic_thresholds,
            'detected_patterns': recent_patterns,
            'recent_adjustments': recent_adjustments,
            'average_effectiveness': (
                sum(self.adjustment_effectiveness) / len(self.adjustment_effectiveness)
                if self.adjustment_effectiveness else 0.0
            ),
            'learning_rate': self.learning_rate,
            'momentum': self.momentum,
            'last_adjustment_time': self.last_adjustment_time,
            'volume_history_size': len(self.volume_history)
        }
    
    def update_thresholds(self, volume_statistics: Dict[str, float]) -> None:
        """Update dynamic thresholds based on observed volume statistics"""
        
        if 'average' in volume_statistics and 'percentile_95' in volume_statistics:
            avg_volume = volume_statistics['average']
            p95_volume = volume_statistics['percentile_95']
            
            # Adjust thresholds based on observed patterns
            self.dynamic_thresholds['low'] = avg_volume * 0.5
            self.dynamic_thresholds['medium'] = avg_volume
            self.dynamic_thresholds['high'] = min(p95_volume, avg_volume * 3.0)
            self.dynamic_thresholds['critical'] = p95_volume * 1.5
    
    def reset_learning_state(self) -> None:
        """Reset learning state for fresh start"""
        self.volume_history.clear()
        self.rate_history.clear()
        self.adjustment_effectiveness.clear()
        self.detected_patterns.clear()
        self.previous_gradient = 0.0
        self.last_adjustment_time = 0.0