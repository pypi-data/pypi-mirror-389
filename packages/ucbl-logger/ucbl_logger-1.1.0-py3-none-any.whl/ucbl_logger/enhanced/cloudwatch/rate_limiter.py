"""
CloudWatch Rate Limiting

Implements sophisticated rate limiting with predictive backoff for CloudWatch API calls.
"""

import time
import random
import threading
from typing import Optional
from collections import deque

from .interfaces import IRateLimiter
from .models import RateLimitState, BackoffStrategy, CloudWatchConfig


class CloudWatchRateLimiter(IRateLimiter):
    """Rate limiter with predictive backoff and burst handling."""
    
    def __init__(self, config: CloudWatchConfig):
        self.config = config
        self.state = RateLimitState()
        self.lock = threading.Lock()
        
        # Request history for predictive analysis
        self.request_history = deque(maxlen=1000)
        self.failure_history = deque(maxlen=100)
        
        # Burst capacity tracking
        self.burst_tokens = config.burst_capacity
        self.last_token_refill = time.time()
        
        # Predictive backoff state
        self.predicted_load = 0.0
        self.load_prediction_window = 60.0  # seconds
    
    def can_make_request(self) -> bool:
        """Check if a request can be made now."""
        with self.lock:
            now = time.time()
            
            # Check if we're in a backoff period
            if now < self.state.backoff_until:
                return False
            
            # Refill burst tokens
            self._refill_burst_tokens(now)
            
            # Check burst capacity
            if self.burst_tokens > 0:
                return True
            
            # Check rate limit
            return self._check_rate_limit(now)
    
    def record_request(self, success: bool) -> None:
        """Record a request attempt."""
        with self.lock:
            now = time.time()
            
            # Update request history
            self.request_history.append({
                'timestamp': now,
                'success': success
            })
            
            # Update state
            self.state.requests_made += 1
            self.state.last_request_time = now
            
            if success:
                # Reset consecutive failures on success
                self.state.consecutive_failures = 0
                # Consume burst token if available
                if self.burst_tokens > 0:
                    self.burst_tokens -= 1
            else:
                # Record failure
                self.state.consecutive_failures += 1
                self.failure_history.append({
                    'timestamp': now,
                    'consecutive_count': self.state.consecutive_failures
                })
                
                # Calculate backoff
                self._calculate_backoff(now)
            
            # Update load prediction
            self._update_load_prediction(now)
    
    def get_delay(self) -> float:
        """Get the delay before next request can be made."""
        with self.lock:
            now = time.time()
            
            # Check backoff period
            if now < self.state.backoff_until:
                return self.state.backoff_until - now
            
            # Check rate limit
            if not self._check_rate_limit(now):
                # Calculate delay based on rate limit
                window_remaining = 1.0 - (now - self.state.window_start)
                if window_remaining > 0:
                    return window_remaining
            
            return 0.0
    
    def reset(self) -> None:
        """Reset the rate limiter state."""
        with self.lock:
            self.state = RateLimitState()
            self.burst_tokens = self.config.burst_capacity
            self.last_token_refill = time.time()
            self.predicted_load = 0.0
    
    def _check_rate_limit(self, now: float) -> bool:
        """Check if request is within rate limit."""
        # Reset window if needed
        if now - self.state.window_start >= 1.0:
            self.state.window_start = now
            self.state.requests_made = 0
        
        # Check if we can make another request in this window
        return self.state.requests_made < self.config.max_requests_per_second
    
    def _refill_burst_tokens(self, now: float) -> None:
        """Refill burst tokens based on time elapsed."""
        time_elapsed = now - self.last_token_refill
        
        # Refill at rate of max_requests_per_second
        tokens_to_add = int(time_elapsed * self.config.max_requests_per_second)
        
        if tokens_to_add > 0:
            self.burst_tokens = min(
                self.config.burst_capacity,
                self.burst_tokens + tokens_to_add
            )
            self.last_token_refill = now
    
    def _calculate_backoff(self, now: float) -> None:
        """Calculate backoff period based on failures."""
        if self.state.consecutive_failures == 0:
            return
        
        if self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = min(
                self.config.base_delay * (2 ** (self.state.consecutive_failures - 1)),
                self.config.max_delay
            )
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = min(
                self.config.base_delay * self.state.consecutive_failures,
                self.config.max_delay
            )
        else:  # FIXED
            delay = self.config.base_delay
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * 0.1 * random.random()
            delay += jitter_amount
        
        # Apply predictive adjustment
        delay = self._apply_predictive_adjustment(delay)
        
        self.state.backoff_until = now + delay
    
    def _apply_predictive_adjustment(self, base_delay: float) -> float:
        """Apply predictive adjustment to backoff delay."""
        # Increase delay if we predict high load
        if self.predicted_load > 0.8:
            return base_delay * (1.0 + self.predicted_load)
        
        return base_delay
    
    def _update_load_prediction(self, now: float) -> None:
        """Update load prediction based on recent request patterns."""
        # Get recent requests within prediction window
        cutoff_time = now - self.load_prediction_window
        recent_requests = [
            req for req in self.request_history 
            if req['timestamp'] > cutoff_time
        ]
        
        if len(recent_requests) < 10:
            return
        
        # Calculate request rate
        time_span = now - recent_requests[0]['timestamp']
        if time_span > 0:
            request_rate = len(recent_requests) / time_span
            
            # Calculate failure rate
            failures = sum(1 for req in recent_requests if not req['success'])
            failure_rate = failures / len(recent_requests)
            
            # Predict load based on rate and failures
            rate_load = min(1.0, request_rate / self.config.max_requests_per_second)
            failure_load = failure_rate * 2.0  # Failures indicate high load
            
            # Combine predictions with exponential smoothing
            new_prediction = max(rate_load, failure_load)
            self.predicted_load = (0.7 * self.predicted_load + 0.3 * new_prediction)
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self.lock:
            now = time.time()
            
            # Calculate recent metrics
            recent_requests = [
                req for req in self.request_history 
                if req['timestamp'] > now - 60
            ]
            
            stats = {
                'requests_made': self.state.requests_made,
                'consecutive_failures': self.state.consecutive_failures,
                'burst_tokens': self.burst_tokens,
                'predicted_load': self.predicted_load,
                'backoff_remaining': max(0, self.state.backoff_until - now),
                'can_make_request': self.can_make_request()
            }
            
            if recent_requests:
                failures = sum(1 for req in recent_requests if not req['success'])
                stats.update({
                    'recent_request_count': len(recent_requests),
                    'recent_failure_rate': failures / len(recent_requests),
                    'recent_request_rate': len(recent_requests) / 60.0
                })
            
            return stats


class AdaptiveRateLimiter(IRateLimiter):
    """Rate limiter that adapts to CloudWatch service capacity."""
    
    def __init__(self, config: CloudWatchConfig):
        self.config = config
        self.base_limiter = CloudWatchRateLimiter(config)
        
        # Adaptive parameters
        self.current_rate_limit = config.max_requests_per_second
        self.min_rate_limit = config.max_requests_per_second * 0.1
        self.max_rate_limit = config.max_requests_per_second * 2.0
        
        # Success/failure tracking for adaptation
        self.recent_outcomes = deque(maxlen=100)
        self.last_adaptation = time.time()
        self.adaptation_interval = 30.0  # seconds
    
    def can_make_request(self) -> bool:
        """Check if request can be made with adaptive rate."""
        # Update config with current adaptive rate
        self.config.max_requests_per_second = self.current_rate_limit
        return self.base_limiter.can_make_request()
    
    def record_request(self, success: bool) -> None:
        """Record request and adapt rate if needed."""
        self.base_limiter.record_request(success)
        
        # Track for adaptation
        self.recent_outcomes.append({
            'timestamp': time.time(),
            'success': success
        })
        
        # Adapt rate periodically
        self._adapt_rate()
    
    def get_delay(self) -> float:
        """Get delay with adaptive rate."""
        return self.base_limiter.get_delay()
    
    def reset(self) -> None:
        """Reset adaptive rate limiter."""
        self.base_limiter.reset()
        self.current_rate_limit = self.config.max_requests_per_second
        self.recent_outcomes.clear()
    
    def get_stats(self) -> dict:
        """Get adaptive rate limiter stats."""
        base_stats = self.base_limiter.get_stats()
        base_stats.update({
            'current_rate_limit': self.current_rate_limit,
            'min_rate_limit': self.min_rate_limit,
            'max_rate_limit': self.max_rate_limit,
            'recent_outcomes_count': len(self.recent_outcomes)
        })
        return base_stats
    
    def _adapt_rate(self) -> None:
        """Adapt rate limit based on recent performance."""
        now = time.time()
        
        # Only adapt periodically
        if now - self.last_adaptation < self.adaptation_interval:
            return
        
        if len(self.recent_outcomes) < 20:
            return
        
        # Calculate success rate
        successes = sum(1 for outcome in self.recent_outcomes if outcome['success'])
        success_rate = successes / len(self.recent_outcomes)
        
        # Adapt rate based on success rate
        if success_rate > 0.95:
            # High success rate, can increase rate
            self.current_rate_limit = min(
                self.max_rate_limit,
                self.current_rate_limit * 1.1
            )
        elif success_rate < 0.8:
            # Low success rate, decrease rate
            self.current_rate_limit = max(
                self.min_rate_limit,
                self.current_rate_limit * 0.9
            )
        
        self.last_adaptation = now