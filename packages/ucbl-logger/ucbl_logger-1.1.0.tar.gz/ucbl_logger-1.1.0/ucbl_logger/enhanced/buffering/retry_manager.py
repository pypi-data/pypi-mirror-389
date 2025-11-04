"""
Production-ready retry logic for log delivery
"""

import time
import random
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from ..models import EnhancedLogEntry
from .models import BufferConfig


class RetryState(Enum):
    """States for retry operations"""
    PENDING = "pending"
    RETRYING = "retrying"
    FAILED = "failed"
    SUCCESS = "success"


@dataclass
class RetryEntry:
    """Entry for retry queue with metadata"""
    log_entry: EnhancedLogEntry
    attempt_count: int = 0
    next_retry_time: float = 0.0
    original_error: Optional[Exception] = None
    state: RetryState = RetryState.PENDING
    priority: int = 0  # Lower number = higher priority
    created_at: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.next_retry_time < other.next_retry_time


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                
                raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "time_until_retry": max(0, self.recovery_timeout - (time.time() - self.last_failure_time))
        }


class RetryManager:
    """Manages retry logic with exponential backoff and jitter"""
    
    def __init__(self, config: BufferConfig):
        self.config = config
        self.retry_queue = []  # Will be used as priority queue
        self.circuit_breaker = CircuitBreaker()
        self._lock = threading.Lock()
        self._running = False
        self._retry_thread = None
        
    def add_retry_entry(self, log_entry: EnhancedLogEntry, error: Exception) -> None:
        """Add entry to retry queue with priority based on log level"""
        priority = self._get_priority(log_entry.level)
        retry_entry = RetryEntry(
            log_entry=log_entry,
            original_error=error,
            priority=priority,
            next_retry_time=time.time() + self._calculate_backoff(0)
        )
        
        with self._lock:
            # Insert maintaining priority order
            inserted = False
            for i, existing_entry in enumerate(self.retry_queue):
                if retry_entry < existing_entry:
                    self.retry_queue.insert(i, retry_entry)
                    inserted = True
                    break
            
            if not inserted:
                self.retry_queue.append(retry_entry)
    
    def _get_priority(self, log_level: str) -> int:
        """Get priority based on log level (lower = higher priority)"""
        priority_map = {
            'CRITICAL': 0,
            'ERROR': 1,
            'WARNING': 2,
            'INFO': 3,
            'DEBUG': 4
        }
        return priority_map.get(log_level.upper(), 5)
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        base_delay = min(
            self.config.retry_backoff_multiplier ** attempt,
            self.config.max_backoff_seconds
        )
        # Add jitter (±25% of base delay)
        jitter = base_delay * 0.25 * (2 * random.random() - 1)
        # Ensure final delay doesn't exceed max_backoff_seconds
        final_delay = max(1.0, base_delay + jitter)
        return min(final_delay, self.config.max_backoff_seconds)
    
    def process_retries(self, delivery_func: Callable[[EnhancedLogEntry], None]) -> Dict[str, int]:
        """Process pending retries"""
        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'circuit_breaker_open': 0
        }
        
        current_time = time.time()
        
        with self._lock:
            # Process entries that are ready for retry
            ready_entries = []
            remaining_entries = []
            
            for entry in self.retry_queue:
                if entry.next_retry_time <= current_time and entry.attempt_count < self.config.max_retry_attempts:
                    ready_entries.append(entry)
                elif entry.attempt_count < self.config.max_retry_attempts:
                    remaining_entries.append(entry)
                # Entries that exceeded max attempts are dropped
            
            self.retry_queue = remaining_entries
        
        # Process ready entries outside the lock
        for entry in ready_entries:
            stats['processed'] += 1
            
            try:
                self.circuit_breaker.call(delivery_func, entry.log_entry)
                entry.state = RetryState.SUCCESS
                stats['succeeded'] += 1
            except Exception as e:
                entry.attempt_count += 1
                entry.original_error = e
                entry.next_retry_time = current_time + self._calculate_backoff(entry.attempt_count)
                entry.state = RetryState.RETRYING
                
                if "Circuit breaker is open" in str(e):
                    stats['circuit_breaker_open'] += 1
                    # Put back in queue for later retry
                    with self._lock:
                        self.retry_queue.append(entry)
                elif entry.attempt_count < self.config.max_retry_attempts:
                    # Put back in queue for retry
                    with self._lock:
                        self.retry_queue.append(entry)
                else:
                    # Max attempts exceeded
                    entry.state = RetryState.FAILED
                    stats['failed'] += 1
        
        return stats
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry queue statistics"""
        with self._lock:
            queue_size = len(self.retry_queue)
            
            # Count by state and priority
            state_counts = {}
            priority_counts = {}
            
            for entry in self.retry_queue:
                state_counts[entry.state.value] = state_counts.get(entry.state.value, 0) + 1
                priority_counts[entry.priority] = priority_counts.get(entry.priority, 0) + 1
        
        return {
            'queue_size': queue_size,
            'state_distribution': state_counts,
            'priority_distribution': priority_counts,
            'circuit_breaker': self.circuit_breaker.get_state()
        }
    
    def clear_failed_entries(self) -> int:
        """Clear entries that have permanently failed"""
        with self._lock:
            original_size = len(self.retry_queue)
            self.retry_queue = [
                entry for entry in self.retry_queue 
                if entry.state != RetryState.FAILED
            ]
            return original_size - len(self.retry_queue)
    
    def start_background_processing(self, delivery_func: Callable[[EnhancedLogEntry], None], 
                                  interval: float = 5.0) -> None:
        """Start background thread for retry processing"""
        if self._running:
            return
        
        self._running = True
        
        def retry_worker():
            while self._running:
                try:
                    self.process_retries(delivery_func)
                    time.sleep(interval)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error in retry worker: {e}")
                    time.sleep(interval)
        
        self._retry_thread = threading.Thread(target=retry_worker, daemon=True)
        self._retry_thread.start()
    
    def stop_background_processing(self) -> None:
        """Stop background retry processing"""
        self._running = False
        if self._retry_thread and self._retry_thread.is_alive():
            self._retry_thread.join(timeout=5.0)