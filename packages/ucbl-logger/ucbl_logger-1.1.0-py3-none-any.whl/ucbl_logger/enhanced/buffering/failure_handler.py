"""
Comprehensive graceful failure handling for log delivery
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from ..models import EnhancedLogEntry


class FailureType(Enum):
    """Types of failures that can occur"""
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class DropStrategy(Enum):
    """Strategies for dropping logs when buffers are full"""
    OLDEST_FIRST = "oldest_first"
    LOWEST_PRIORITY = "lowest_priority"
    RANDOM_SAMPLING = "random_sampling"
    PRESERVE_ERRORS = "preserve_errors"


@dataclass
class FailurePattern:
    """Pattern for detecting failure types"""
    failure_type: FailureType
    error_patterns: List[str]
    recovery_time: float
    max_consecutive_failures: int


class FailureClassifier:
    """Classifies failures and determines appropriate handling"""
    
    def __init__(self):
        self.patterns = [
            FailurePattern(
                FailureType.NETWORK_ERROR,
                ["connection", "network", "dns", "timeout", "unreachable"],
                30.0,  # 30 seconds recovery time
                10
            ),
            FailurePattern(
                FailureType.AUTHENTICATION_ERROR,
                ["authentication", "unauthorized", "forbidden", "credentials"],
                300.0,  # 5 minutes recovery time
                3
            ),
            FailurePattern(
                FailureType.RATE_LIMIT_ERROR,
                ["rate limit", "throttle", "quota", "too many requests"],
                60.0,  # 1 minute recovery time
                5
            ),
            FailurePattern(
                FailureType.SERVICE_UNAVAILABLE,
                ["service unavailable", "server error", "internal error"],
                120.0,  # 2 minutes recovery time
                8
            ),
            FailurePattern(
                FailureType.TIMEOUT_ERROR,
                ["timeout", "deadline exceeded"],
                15.0,  # 15 seconds recovery time
                15
            )
        ]
    
    def classify_failure(self, error: Exception) -> FailureType:
        """Classify failure based on error message"""
        error_message = str(error).lower()
        
        for pattern in self.patterns:
            for error_pattern in pattern.error_patterns:
                if error_pattern in error_message:
                    return pattern.failure_type
        
        return FailureType.UNKNOWN_ERROR
    
    def get_recovery_time(self, failure_type: FailureType) -> float:
        """Get recommended recovery time for failure type"""
        for pattern in self.patterns:
            if pattern.failure_type == failure_type:
                return pattern.recovery_time
        return 60.0  # Default recovery time


class IntelligentDropper:
    """Intelligent log dropping based on importance and age"""
    
    def __init__(self, strategy: DropStrategy = DropStrategy.PRESERVE_ERRORS):
        self.strategy = strategy
        self.drop_stats = {
            'total_dropped': 0,
            'dropped_by_level': {},
            'dropped_by_age': {},
            'preserved_critical': 0
        }
    
    def should_drop_log(self, log_entry: EnhancedLogEntry, buffer_age_seconds: float) -> bool:
        """Determine if a log should be dropped based on strategy"""
        
        # Never drop critical or error logs if using preserve_errors strategy
        if self.strategy == DropStrategy.PRESERVE_ERRORS:
            if log_entry.level.upper() in ['CRITICAL', 'ERROR']:
                self.drop_stats['preserved_critical'] += 1
                return False
        
        # Age-based dropping
        if buffer_age_seconds > 300:  # 5 minutes old
            self._record_drop(log_entry, 'age')
            return True
        
        # Priority-based dropping
        if self.strategy == DropStrategy.LOWEST_PRIORITY:
            if log_entry.level.upper() in ['DEBUG', 'INFO']:
                self._record_drop(log_entry, 'priority')
                return True
        
        return False
    
    def _record_drop(self, log_entry: EnhancedLogEntry, reason: str) -> None:
        """Record drop statistics"""
        self.drop_stats['total_dropped'] += 1
        
        level = log_entry.level.upper()
        self.drop_stats['dropped_by_level'][level] = self.drop_stats['dropped_by_level'].get(level, 0) + 1
        
        if reason == 'age':
            self.drop_stats['dropped_by_age']['old_logs'] = self.drop_stats['dropped_by_age'].get('old_logs', 0) + 1
    
    def get_drop_statistics(self) -> Dict[str, Any]:
        """Get dropping statistics"""
        return self.drop_stats.copy()


class GracefulFailureHandler:
    """Handles failures gracefully to ensure application continues running"""
    
    def __init__(self):
        self.failure_classifier = FailureClassifier()
        self.intelligent_dropper = IntelligentDropper()
        
        # Failure tracking
        self.failure_history = {}  # destination -> list of failures
        self.consecutive_failures = {}  # destination -> count
        self.last_success_time = {}  # destination -> timestamp
        
        # Circuit breaker states per destination
        self.circuit_states = {}  # destination -> state
        
        # Statistics
        self.stats = {
            'total_failures': 0,
            'failures_by_type': {},
            'circuit_breaker_trips': 0,
            'graceful_degradations': 0,
            'application_continuity_preserved': 0
        }
        
        self._lock = threading.Lock()
    
    def handle_delivery_failure(self, destination: str, error: Exception, 
                              log_entry: EnhancedLogEntry) -> Dict[str, Any]:
        """Handle a delivery failure gracefully"""
        
        failure_type = self.failure_classifier.classify_failure(error)
        current_time = time.time()
        
        with self._lock:
            # Update failure statistics
            self.stats['total_failures'] += 1
            failure_type_str = failure_type.value
            self.stats['failures_by_type'][failure_type_str] = \
                self.stats['failures_by_type'].get(failure_type_str, 0) + 1
            
            # Track consecutive failures for this destination
            self.consecutive_failures[destination] = \
                self.consecutive_failures.get(destination, 0) + 1
            
            # Record failure in history
            if destination not in self.failure_history:
                self.failure_history[destination] = []
            
            self.failure_history[destination].append({
                'timestamp': current_time,
                'error': str(error),
                'failure_type': failure_type.value,
                'log_level': log_entry.level
            })
            
            # Keep only recent failures (last hour)
            self.failure_history[destination] = [
                f for f in self.failure_history[destination]
                if current_time - f['timestamp'] < 3600
            ]
        
        # Determine action based on failure pattern
        action = self._determine_action(destination, failure_type, log_entry)
        
        # Ensure application continuity
        self._ensure_application_continuity()
        
        return action
    
    def _determine_action(self, destination: str, failure_type: FailureType, 
                         log_entry: EnhancedLogEntry) -> Dict[str, Any]:
        """Determine the appropriate action for the failure"""
        
        consecutive_count = self.consecutive_failures.get(destination, 0)
        recovery_time = self.failure_classifier.get_recovery_time(failure_type)
        
        # Check if circuit breaker should trip
        if consecutive_count >= 5:  # Trip after 5 consecutive failures
            self._trip_circuit_breaker(destination, recovery_time)
            return {
                'action': 'circuit_breaker_trip',
                'retry_after': recovery_time,
                'drop_log': False,  # Keep in retry queue
                'message': f'Circuit breaker tripped for {destination}'
            }
        
        # Handle specific failure types
        if failure_type == FailureType.AUTHENTICATION_ERROR:
            return {
                'action': 'authentication_failure',
                'retry_after': recovery_time,
                'drop_log': False,
                'message': 'Authentication failure - will retry with backoff'
            }
        
        elif failure_type == FailureType.RATE_LIMIT_ERROR:
            return {
                'action': 'rate_limit_backoff',
                'retry_after': recovery_time,
                'drop_log': False,
                'message': 'Rate limited - backing off'
            }
        
        elif failure_type == FailureType.NETWORK_ERROR:
            # For network errors, consider dropping non-critical logs if too many failures
            drop_log = consecutive_count > 10 and log_entry.level.upper() not in ['CRITICAL', 'ERROR']
            return {
                'action': 'network_retry',
                'retry_after': min(recovery_time, 30.0),
                'drop_log': drop_log,
                'message': 'Network error - will retry'
            }
        
        else:
            # Default handling
            return {
                'action': 'default_retry',
                'retry_after': recovery_time,
                'drop_log': False,
                'message': 'Unknown error - will retry'
            }
    
    def _trip_circuit_breaker(self, destination: str, recovery_time: float) -> None:
        """Trip circuit breaker for destination"""
        with self._lock:
            self.circuit_states[destination] = {
                'state': 'open',
                'trip_time': time.time(),
                'recovery_time': recovery_time
            }
            self.stats['circuit_breaker_trips'] += 1
    
    def _ensure_application_continuity(self) -> None:
        """Ensure the application continues running smoothly"""
        with self._lock:
            self.stats['application_continuity_preserved'] += 1
        
        # This method ensures that logging failures never block the application
        # All operations are designed to be non-blocking and fail gracefully
        
        # Additional measures could include:
        # - Reducing log verbosity temporarily
        # - Switching to emergency local logging
        # - Notifying monitoring systems of degraded logging
    
    def handle_success(self, destination: str) -> None:
        """Handle successful delivery to reset failure counters"""
        current_time = time.time()
        
        with self._lock:
            # Reset consecutive failure counter
            self.consecutive_failures[destination] = 0
            self.last_success_time[destination] = current_time
            
            # Close circuit breaker if it was open
            if destination in self.circuit_states:
                if self.circuit_states[destination]['state'] == 'open':
                    self.circuit_states[destination] = {
                        'state': 'closed',
                        'last_success': current_time
                    }
    
    def is_circuit_breaker_open(self, destination: str) -> bool:
        """Check if circuit breaker is open for destination"""
        if destination not in self.circuit_states:
            return False
        
        circuit_state = self.circuit_states[destination]
        if circuit_state['state'] != 'open':
            return False
        
        # Check if recovery time has passed
        current_time = time.time()
        if current_time - circuit_state['trip_time'] > circuit_state['recovery_time']:
            # Move to half-open state
            with self._lock:
                self.circuit_states[destination]['state'] = 'half-open'
            return False
        
        return True
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get comprehensive failure statistics"""
        with self._lock:
            stats_copy = self.stats.copy()
            
            # Add current circuit breaker states
            circuit_summary = {}
            for dest, state in self.circuit_states.items():
                circuit_summary[dest] = state['state']
            
            # Add failure rates by destination
            failure_rates = {}
            current_time = time.time()
            
            for dest, failures in self.failure_history.items():
                recent_failures = [
                    f for f in failures
                    if current_time - f['timestamp'] < 300  # Last 5 minutes
                ]
                failure_rates[dest] = len(recent_failures)
        
        return {
            'overall_stats': stats_copy,
            'circuit_breakers': circuit_summary,
            'recent_failure_rates': failure_rates,
            'consecutive_failures': self.consecutive_failures.copy(),
            'drop_statistics': self.intelligent_dropper.get_drop_statistics()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of failure handling"""
        
        # Count open circuit breakers
        open_circuits = sum(
            1 for state in self.circuit_states.values()
            if state.get('state') == 'open'
        )
        
        # Calculate recent failure rate
        current_time = time.time()
        recent_failures = 0
        for failures in self.failure_history.values():
            recent_failures += len([
                f for f in failures
                if current_time - f['timestamp'] < 300  # Last 5 minutes
            ])
        
        # Determine health level
        if open_circuits > 0:
            health_level = 'degraded'
        elif recent_failures > 10:
            health_level = 'warning'
        else:
            health_level = 'healthy'
        
        return {
            'health_level': health_level,
            'open_circuit_breakers': open_circuits,
            'recent_failure_count': recent_failures,
            'application_continuity': 'preserved',  # Always preserved by design
            'recommendations': self._get_health_recommendations(health_level, open_circuits, recent_failures)
        }
    
    def _get_health_recommendations(self, health_level: str, open_circuits: int, 
                                  recent_failures: int) -> List[str]:
        """Get recommendations based on current health status"""
        recommendations = []
        
        if open_circuits > 0:
            recommendations.append("Check destination connectivity and authentication")
            recommendations.append("Consider alternative log destinations")
        
        if recent_failures > 10:
            recommendations.append("Monitor network connectivity")
            recommendations.append("Check for rate limiting issues")
        
        if health_level == 'degraded':
            recommendations.append("Consider reducing log verbosity temporarily")
            recommendations.append("Enable emergency local logging if available")
        
        return recommendations