"""
Intelligent Log Batching for CloudWatch

Implements adaptive batching strategies for optimal CloudWatch delivery efficiency.
"""

import time
import threading
from typing import Optional, List
from collections import deque

from .interfaces import IBatcher
from .models import LogEntry, LogBatch, BatchConfig


class IntelligentBatcher(IBatcher):
    """Intelligent batcher with adaptive sizing and timing."""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.current_batch = LogBatch()
        self.batch_history = deque(maxlen=100)  # Keep history for adaptive sizing
        self.lock = threading.Lock()
        
        # Adaptive sizing state
        self.current_target_size = config.target_batch_size
        self.last_adjustment_time = time.time()
        self.delivery_times = deque(maxlen=50)
        
    def add_entry(self, entry: LogEntry) -> Optional[LogBatch]:
        """Add an entry to the current batch. Returns completed batch if ready."""
        with self.lock:
            self.current_batch.add_entry(entry)
            
            # Check if batch is ready
            if self._is_batch_ready():
                ready_batch = self.current_batch
                self.current_batch = LogBatch()
                self._record_batch_completion(ready_batch)
                return ready_batch
            
            return None
    
    def get_ready_batch(self) -> Optional[LogBatch]:
        """Get a batch that's ready for delivery based on timeout."""
        with self.lock:
            if self._is_batch_timeout() and not self.current_batch.is_empty():
                ready_batch = self.current_batch
                self.current_batch = LogBatch()
                self._record_batch_completion(ready_batch)
                return ready_batch
            
            return None
    
    def force_flush(self) -> Optional[LogBatch]:
        """Force flush the current batch."""
        with self.lock:
            if not self.current_batch.is_empty():
                ready_batch = self.current_batch
                self.current_batch = LogBatch()
                self._record_batch_completion(ready_batch)
                return ready_batch
            
            return None
    
    def should_create_batch(self) -> bool:
        """Check if a new batch should be created."""
        with self.lock:
            return self.current_batch.is_empty()
    
    def _is_batch_ready(self) -> bool:
        """Check if the current batch is ready for delivery."""
        batch_size = self.current_batch.size()
        
        # Check size limits
        if batch_size >= self.config.max_batch_size:
            return True
        
        # Check adaptive target size
        if batch_size >= self.current_target_size:
            return True
        
        # Check minimum size with timeout
        if (batch_size >= self.config.min_batch_size and 
            self._is_batch_timeout()):
            return True
        
        return False
    
    def _is_batch_timeout(self) -> bool:
        """Check if the current batch has timed out."""
        if self.current_batch.is_empty():
            return False
        
        age = time.time() - self.current_batch.created_at
        return age >= self.config.batch_timeout
    
    def _record_batch_completion(self, batch: LogBatch) -> None:
        """Record batch completion for adaptive sizing."""
        self.batch_history.append({
            'size': batch.size(),
            'created_at': batch.created_at,
            'completed_at': time.time(),
            'age': time.time() - batch.created_at
        })
        
        # Adjust target size if adaptive sizing is enabled
        if self.config.adaptive_sizing:
            self._adjust_target_size()
    
    def _adjust_target_size(self) -> None:
        """Adjust target batch size based on recent performance."""
        now = time.time()
        
        # Only adjust every 30 seconds
        if now - self.last_adjustment_time < 30:
            return
        
        if len(self.batch_history) < 10:
            return
        
        # Calculate recent metrics
        recent_batches = list(self.batch_history)[-10:]
        avg_age = sum(b['age'] for b in recent_batches) / len(recent_batches)
        avg_size = sum(b['size'] for b in recent_batches) / len(recent_batches)
        
        # Adjust based on batch age vs timeout
        if avg_age > self.config.batch_timeout * 0.8:
            # Batches are timing out, reduce target size
            adjustment = -int(self.current_target_size * self.config.size_adjustment_factor)
        elif avg_age < self.config.batch_timeout * 0.3:
            # Batches are filling quickly, increase target size
            adjustment = int(self.current_target_size * self.config.size_adjustment_factor)
        else:
            # Current size is working well
            adjustment = 0
        
        # Apply adjustment with bounds checking
        new_target = self.current_target_size + adjustment
        new_target = max(self.config.min_batch_size, 
                        min(self.config.max_batch_size, new_target))
        
        if new_target != self.current_target_size:
            self.current_target_size = new_target
            self.last_adjustment_time = now
    
    def get_stats(self) -> dict:
        """Get batching statistics."""
        with self.lock:
            recent_batches = list(self.batch_history)[-20:] if self.batch_history else []
            
            stats = {
                'current_batch_size': self.current_batch.size(),
                'current_target_size': self.current_target_size,
                'total_batches_processed': len(self.batch_history),
                'current_batch_age': time.time() - self.current_batch.created_at if not self.current_batch.is_empty() else 0
            }
            
            if recent_batches:
                stats.update({
                    'avg_batch_size': sum(b['size'] for b in recent_batches) / len(recent_batches),
                    'avg_batch_age': sum(b['age'] for b in recent_batches) / len(recent_batches),
                    'timeout_rate': sum(1 for b in recent_batches if b['age'] >= self.config.batch_timeout * 0.9) / len(recent_batches)
                })
            
            return stats


class PriorityBatcher(IBatcher):
    """Batcher that handles different priority levels."""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.high_priority_batch = LogBatch()
        self.normal_priority_batch = LogBatch()
        self.lock = threading.Lock()
    
    def add_entry(self, entry: LogEntry) -> Optional[LogBatch]:
        """Add entry to appropriate priority batch."""
        with self.lock:
            # Determine priority based on log level
            is_high_priority = entry.log_level.upper() in ['ERROR', 'CRITICAL', 'FATAL']
            
            if is_high_priority:
                self.high_priority_batch.add_entry(entry)
                # High priority batches are smaller and sent more frequently
                if self.high_priority_batch.size() >= self.config.min_batch_size:
                    ready_batch = self.high_priority_batch
                    self.high_priority_batch = LogBatch()
                    return ready_batch
            else:
                self.normal_priority_batch.add_entry(entry)
                if self.normal_priority_batch.size() >= self.config.target_batch_size:
                    ready_batch = self.normal_priority_batch
                    self.normal_priority_batch = LogBatch()
                    return ready_batch
            
            return None
    
    def get_ready_batch(self) -> Optional[LogBatch]:
        """Get ready batch, prioritizing high priority logs."""
        with self.lock:
            # Check high priority first
            if (not self.high_priority_batch.is_empty() and 
                time.time() - self.high_priority_batch.created_at >= self.config.batch_timeout / 2):
                ready_batch = self.high_priority_batch
                self.high_priority_batch = LogBatch()
                return ready_batch
            
            # Check normal priority
            if (not self.normal_priority_batch.is_empty() and 
                time.time() - self.normal_priority_batch.created_at >= self.config.batch_timeout):
                ready_batch = self.normal_priority_batch
                self.normal_priority_batch = LogBatch()
                return ready_batch
            
            return None
    
    def force_flush(self) -> Optional[LogBatch]:
        """Force flush both batches, prioritizing high priority."""
        with self.lock:
            # Flush high priority first
            if not self.high_priority_batch.is_empty():
                ready_batch = self.high_priority_batch
                self.high_priority_batch = LogBatch()
                return ready_batch
            
            # Then normal priority
            if not self.normal_priority_batch.is_empty():
                ready_batch = self.normal_priority_batch
                self.normal_priority_batch = LogBatch()
                return ready_batch
            
            return None
    
    def should_create_batch(self) -> bool:
        """Check if new batches should be created."""
        with self.lock:
            return (self.high_priority_batch.is_empty() and 
                   self.normal_priority_batch.is_empty())