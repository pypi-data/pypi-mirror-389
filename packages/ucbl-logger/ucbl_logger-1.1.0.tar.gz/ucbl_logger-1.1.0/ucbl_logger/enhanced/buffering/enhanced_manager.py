"""
Enhanced buffer manager with production-ready retry logic and memory pressure handling
"""

import time
import threading
import psutil
from collections import deque
from typing import Dict, Any, List, Callable, Optional
from ..models import EnhancedLogEntry
from .models import BufferConfig
from .interfaces import IBufferManager
from .retry_manager import RetryManager, RetryState
from .failure_handler import GracefulFailureHandler
from .monitoring import BufferMonitor


class MemoryPressureMonitor:
    """Monitor system memory pressure and trigger buffer management actions"""
    
    def __init__(self, warning_threshold: float = 0.8, critical_threshold: float = 0.9):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._last_check = 0.0
        self._check_interval = 5.0  # Check every 5 seconds
    
    def get_memory_pressure(self) -> Dict[str, Any]:
        """Get current memory pressure information"""
        current_time = time.time()
        
        # Cache memory info for a few seconds to avoid excessive system calls
        if current_time - self._last_check < self._check_interval:
            return getattr(self, '_cached_pressure', {'level': 'normal', 'usage': 0.0})
        
        try:
            memory = psutil.virtual_memory()
            usage_ratio = memory.percent / 100.0
            
            if usage_ratio >= self.critical_threshold:
                level = 'critical'
            elif usage_ratio >= self.warning_threshold:
                level = 'warning'
            else:
                level = 'normal'
            
            pressure_info = {
                'level': level,
                'usage': usage_ratio,
                'available_mb': memory.available / (1024 * 1024),
                'total_mb': memory.total / (1024 * 1024)
            }
            
            self._cached_pressure = pressure_info
            self._last_check = current_time
            
            return pressure_info
            
        except Exception:
            # Fallback if psutil fails
            return {'level': 'unknown', 'usage': 0.0}


class PriorityQueue:
    """Priority queue for log entries with memory-efficient operations"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.queues = {
            0: deque(),  # CRITICAL
            1: deque(),  # ERROR  
            2: deque(),  # WARNING
            3: deque(),  # INFO
            4: deque(),  # DEBUG
            5: deque()   # OTHER
        }
        self._size = 0
        self._lock = threading.Lock()
    
    def put(self, log_entry: EnhancedLogEntry) -> bool:
        """Add log entry to appropriate priority queue"""
        priority = self._get_priority(log_entry.level)
        
        with self._lock:
            if self._size >= self.max_size:
                # Try to drop lower priority items first
                if not self._make_space_for_priority(priority):
                    return False  # Could not make space
            
            self.queues[priority].append(log_entry)
            self._size += 1
            return True
    
    def get(self) -> Optional[EnhancedLogEntry]:
        """Get highest priority log entry"""
        with self._lock:
            for priority in sorted(self.queues.keys()):
                if self.queues[priority]:
                    entry = self.queues[priority].popleft()
                    self._size -= 1
                    return entry
            return None
    
    def _get_priority(self, log_level: str) -> int:
        """Get priority based on log level"""
        priority_map = {
            'CRITICAL': 0,
            'ERROR': 1,
            'WARNING': 2,
            'INFO': 3,
            'DEBUG': 4
        }
        return priority_map.get(log_level.upper(), 5)
    
    def _make_space_for_priority(self, new_priority: int) -> bool:
        """Try to make space by dropping lower priority items"""
        # Try to drop items with lower priority (higher number)
        for priority in reversed(sorted(self.queues.keys())):
            if priority > new_priority and self.queues[priority]:
                self.queues[priority].popleft()
                self._size -= 1
                return True
        return False
    
    def size(self) -> int:
        """Get total size across all priority queues"""
        return self._size
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics by priority level"""
        with self._lock:
            return {str(priority): len(queue) for priority, queue in self.queues.items()}
    
    def clear(self) -> int:
        """Clear all queues and return number of dropped items"""
        with self._lock:
            dropped = self._size
            for queue in self.queues.values():
                queue.clear()
            self._size = 0
            return dropped


class EnhancedBufferManager(IBufferManager):
    """Enhanced buffer manager with production-ready features"""
    
    def __init__(self, config: BufferConfig, delivery_func: Optional[Callable[[EnhancedLogEntry], None]] = None):
        self.config = config
        self.delivery_func = delivery_func
        
        # Core components
        self.buffer = PriorityQueue(config.max_size)
        self.retry_manager = RetryManager(config)
        self.memory_monitor = MemoryPressureMonitor()
        self.failure_handler = GracefulFailureHandler()
        self.monitor = BufferMonitor()
        
        # Statistics and monitoring
        self.stats = {
            'total_logs': 0,
            'dropped_logs': 0,
            'failed_deliveries': 0,
            'successful_deliveries': 0,
            'memory_pressure_drops': 0,
            'buffer_full_drops': 0
        }
        
        # Threading
        self._lock = threading.Lock()
        self._flush_thread = None
        self._running = False
        
        # Start background processing if delivery function provided
        if self.delivery_func:
            self.start_background_processing()
    
    def add_log_entry(self, log_entry: EnhancedLogEntry) -> None:
        """Add a log entry to the buffer with memory pressure handling"""
        with self._lock:
            self.stats['total_logs'] += 1
        
        # Check memory pressure before adding
        memory_pressure = self.memory_monitor.get_memory_pressure()
        
        if memory_pressure['level'] == 'critical':
            # In critical memory pressure, only accept CRITICAL and ERROR logs
            if log_entry.level.upper() not in ['CRITICAL', 'ERROR']:
                with self._lock:
                    self.stats['memory_pressure_drops'] += 1
                return
        
        # Try to add to buffer
        if not self.buffer.put(log_entry):
            with self._lock:
                self.stats['buffer_full_drops'] += 1
    
    def flush_buffer(self) -> None:
        """Flush buffered logs to configured outputs"""
        if not self.delivery_func:
            return
        
        processed_count = 0
        
        while True:
            log_entry = self.buffer.get()
            if log_entry is None:
                break
            
            try:
                self.delivery_func(log_entry)
                # Record success with failure handler
                self.failure_handler.handle_success("default")
                with self._lock:
                    self.stats['successful_deliveries'] += 1
                processed_count += 1
                
            except Exception as e:
                self.handle_delivery_failure(log_entry, e)
        
        # Also process retries
        if processed_count > 0:
            retry_stats = self.retry_manager.process_retries(self.delivery_func)
            with self._lock:
                self.stats['successful_deliveries'] += retry_stats['succeeded']
    
    def handle_delivery_failure(self, log_entry: EnhancedLogEntry, error: Exception) -> None:
        """Handle failed log delivery with graceful failure handling"""
        with self._lock:
            self.stats['failed_deliveries'] += 1
        
        # Use graceful failure handler to determine action
        destination = "default"  # Could be made configurable
        action = self.failure_handler.handle_delivery_failure(destination, error, log_entry)
        
        # Take action based on failure handler recommendation
        if not action.get('drop_log', False):
            # Add to retry queue if not dropping
            self.retry_manager.add_retry_entry(log_entry, error)
        else:
            # Log was dropped due to failure pattern
            with self._lock:
                self.stats['dropped_logs'] += 1
    
    def get_buffer_statistics(self) -> Dict[str, Any]:
        """Get comprehensive buffer usage and delivery statistics"""
        memory_pressure = self.memory_monitor.get_memory_pressure()
        retry_stats = self.retry_manager.get_retry_statistics()
        
        with self._lock:
            stats_copy = self.stats.copy()
        
        failure_stats = self.failure_handler.get_failure_statistics()
        failure_health = self.failure_handler.get_health_status()
        
        # Record metrics for monitoring
        buffer_stats_for_monitoring = {
            'buffer_usage_percent': (self.buffer.size() / self.config.max_size) * 100,
            'memory_pressure': memory_pressure,
            'delivery_stats': stats_copy,
            'retry_queue': retry_stats
        }
        self.monitor.record_buffer_metrics(buffer_stats_for_monitoring)
        
        return {
            'buffer_size': self.buffer.size(),
            'max_buffer_size': self.config.max_size,
            'buffer_usage_percent': (self.buffer.size() / self.config.max_size) * 100,
            'priority_distribution': self.buffer.get_statistics(),
            'memory_pressure': memory_pressure,
            'retry_queue': retry_stats,
            'delivery_stats': stats_copy,
            'failure_handling': failure_stats,
            'health_indicators': {
                'buffer_healthy': self.is_buffer_healthy(),
                'memory_pressure_level': memory_pressure['level'],
                'circuit_breaker_state': retry_stats['circuit_breaker']['state'],
                'failure_handler_health': failure_health['health_level'],
                'application_continuity': failure_health['application_continuity']
            },
            'monitoring': self.monitor.get_dashboard_data()
        }
    
    def is_buffer_healthy(self) -> bool:
        """Check if buffer is operating within healthy parameters"""
        buffer_usage = self.buffer.size() / self.config.max_size
        memory_pressure = self.memory_monitor.get_memory_pressure()
        retry_stats = self.retry_manager.get_retry_statistics()
        
        # Consider unhealthy if:
        # - Buffer is more than 80% full
        # - Memory pressure is critical
        # - Circuit breaker is open
        # - Too many items in retry queue
        
        if buffer_usage > 0.8:
            return False
        
        if memory_pressure['level'] == 'critical':
            return False
        
        if retry_stats['circuit_breaker']['state'] == 'open':
            return False
        
        if retry_stats['queue_size'] > self.config.max_size * 0.1:  # More than 10% of buffer size
            return False
        
        return True
    
    def clear_buffer(self) -> None:
        """Clear all buffered logs (emergency operation)"""
        dropped_count = self.buffer.clear()
        failed_retries_cleared = self.retry_manager.clear_failed_entries()
        
        with self._lock:
            self.stats['dropped_logs'] += dropped_count + failed_retries_cleared
    
    def start_background_processing(self) -> None:
        """Start background thread for periodic flushing"""
        if self._running or not self.delivery_func:
            return
        
        self._running = True
        
        def flush_worker():
            while self._running:
                try:
                    self.flush_buffer()
                    time.sleep(self.config.flush_interval_seconds)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error in flush worker: {e}")
                    time.sleep(self.config.flush_interval_seconds)
        
        self._flush_thread = threading.Thread(target=flush_worker, daemon=True)
        self._flush_thread.start()
        
        # Also start retry processing
        self.retry_manager.start_background_processing(self.delivery_func)
    
    def stop_background_processing(self) -> None:
        """Stop background processing threads"""
        self._running = False
        
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5.0)
        
        self.retry_manager.stop_background_processing()
    
    def get_health_alerts(self) -> List[Dict[str, Any]]:
        """Get list of current health alerts"""
        alerts = []
        
        # Buffer usage alerts
        buffer_usage = self.buffer.size() / self.config.max_size
        if buffer_usage > 0.9:
            alerts.append({
                'type': 'buffer_critical',
                'message': f'Buffer usage critical: {buffer_usage:.1%}',
                'severity': 'critical'
            })
        elif buffer_usage > 0.8:
            alerts.append({
                'type': 'buffer_warning',
                'message': f'Buffer usage high: {buffer_usage:.1%}',
                'severity': 'warning'
            })
        
        # Memory pressure alerts
        memory_pressure = self.memory_monitor.get_memory_pressure()
        if memory_pressure['level'] == 'critical':
            alerts.append({
                'type': 'memory_critical',
                'message': f'Memory usage critical: {memory_pressure["usage"]:.1%}',
                'severity': 'critical'
            })
        elif memory_pressure['level'] == 'warning':
            alerts.append({
                'type': 'memory_warning',
                'message': f'Memory usage high: {memory_pressure["usage"]:.1%}',
                'severity': 'warning'
            })
        
        # Circuit breaker alerts
        retry_stats = self.retry_manager.get_retry_statistics()
        if retry_stats['circuit_breaker']['state'] == 'open':
            alerts.append({
                'type': 'circuit_breaker_open',
                'message': 'Circuit breaker is open - log delivery failing',
                'severity': 'critical'
            })
        
        # Retry queue alerts
        if retry_stats['queue_size'] > self.config.max_size * 0.2:
            alerts.append({
                'type': 'retry_queue_high',
                'message': f'Retry queue size high: {retry_stats["queue_size"]}',
                'severity': 'warning'
            })
        
        # Add monitoring alerts
        monitoring_analysis = self.monitor.analyze_trends_and_check_thresholds()
        for monitoring_alert in monitoring_analysis['alerts']:
            alerts.append({
                'type': f'monitoring_{monitoring_alert.metric_name}',
                'message': monitoring_alert.message,
                'severity': monitoring_alert.severity.value,
                'recommendations': monitoring_alert.recommendations
            })
        
        return alerts