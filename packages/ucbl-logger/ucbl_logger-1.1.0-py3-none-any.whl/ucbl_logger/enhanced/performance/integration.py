"""
Performance monitoring integration with logging system
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import asdict
from .monitor import EnhancedPerformanceMonitor
from .models import SystemMetrics, PerformanceAlert, PerformanceThresholds


class PerformanceLoggingIntegration:
    """Integrates performance monitoring with the logging system"""
    
    def __init__(self, 
                 performance_monitor: EnhancedPerformanceMonitor,
                 logger: Optional[logging.Logger] = None,
                 periodic_logging_interval: int = 300,  # 5 minutes
                 alert_callback: Optional[Callable[[PerformanceAlert], None]] = None):
        """
        Initialize performance logging integration
        
        Args:
            performance_monitor: The performance monitor instance
            logger: Logger instance to use for performance logging
            periodic_logging_interval: Interval in seconds for periodic metric logging
            alert_callback: Optional callback function for performance alerts
        """
        self.performance_monitor = performance_monitor
        self.logger = logger or logging.getLogger(__name__)
        self.periodic_logging_interval = periodic_logging_interval
        self.alert_callback = alert_callback
        
        # Integration state
        self.integration_active = False
        self.periodic_logging_thread: Optional[threading.Thread] = None
        self.last_alert_times: Dict[str, float] = {}
        self.alert_cooldown = 60  # 1 minute cooldown between same alerts
        
        # Performance-aware sampling state
        self.current_system_load = 0.0
        self.sampling_adjustment_enabled = True
        self.base_sampling_rate = 1.0
        self.load_threshold_for_sampling = 80.0  # CPU % threshold
    
    def add_performance_context_to_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Add current performance metrics to a log entry"""
        try:
            # Get current performance summary
            load_summary = self.performance_monitor.get_current_load_summary()
            
            # Add performance context
            log_entry['performance_context'] = {
                'cpu_percent': load_summary.get('cpu_percent', 0.0),
                'memory_percent': load_summary.get('memory_percent', 0.0),
                'load_avg': load_summary.get('load_avg_1min', 0.0),
                'network_mbps': load_summary.get('network_mbps_total', 0.0),
                'timestamp': time.time()
            }
            
            # Update current system load for sampling decisions
            self.current_system_load = load_summary.get('cpu_percent', 0.0)
            
        except Exception as e:
            self.logger.error(f"Error adding performance context to log entry: {e}")
        
        return log_entry
    
    def should_sample_based_on_performance(self, log_level: str) -> bool:
        """
        Determine if a log should be sampled based on current system performance
        
        Returns True if the log should be kept, False if it should be dropped
        """
        if not self.sampling_adjustment_enabled:
            return True
        
        # Always keep error and critical logs
        if log_level.upper() in ['ERROR', 'CRITICAL', 'FATAL']:
            return True
        
        # Adjust sampling rate based on system load
        if self.current_system_load > self.load_threshold_for_sampling:
            # High load - reduce sampling for non-critical logs
            load_factor = min(self.current_system_load / 100.0, 1.0)
            adjusted_rate = self.base_sampling_rate * (1.0 - load_factor * 0.7)  # Reduce up to 70%
            
            # Use time-based sampling decision
            return (time.time() % 1.0) < adjusted_rate
        
        return True
    
    def get_performance_aware_sampling_rate(self) -> float:
        """Get the current sampling rate adjusted for system performance"""
        if not self.sampling_adjustment_enabled:
            return self.base_sampling_rate
        
        if self.current_system_load > self.load_threshold_for_sampling:
            load_factor = min(self.current_system_load / 100.0, 1.0)
            return self.base_sampling_rate * (1.0 - load_factor * 0.7)
        
        return self.base_sampling_rate
    
    def log_performance_metrics(self, metrics: Optional[SystemMetrics] = None) -> None:
        """Log current performance metrics"""
        try:
            if metrics is None:
                metrics = self.performance_monitor.collect_system_metrics()
            
            # Create performance log entry
            performance_data = {
                'event_type': 'performance_metrics',
                'timestamp': metrics.timestamp,
                'metrics': metrics.to_dict(),
                'system_load_summary': {
                    'cpu_percent': metrics.cpu.percent,
                    'memory_percent': metrics.memory.percent,
                    'disk_usage_percent': metrics.disk.usage_percent,
                    'load_avg_1min': metrics.cpu.load_avg_1min,
                    'network_bandwidth_mbps': (
                        (metrics.network.bytes_sent_per_sec + metrics.network.bytes_recv_per_sec) * 8 
                        / (1024 * 1024)
                    )
                }
            }
            
            self.logger.info(f"Performance metrics: {performance_data}")
            
            # Check for alerts
            alerts = self.performance_monitor.generate_performance_alerts(metrics)
            for alert in alerts:
                self._handle_performance_alert(alert)
                
        except Exception as e:
            self.logger.error(f"Error logging performance metrics: {e}")
    
    def _handle_performance_alert(self, alert: PerformanceAlert) -> None:
        """Handle a performance alert with cooldown logic"""
        try:
            alert_key = f"{alert.metric}_{alert.level}"
            current_time = time.time()
            
            # Check cooldown
            if alert_key in self.last_alert_times:
                if current_time - self.last_alert_times[alert_key] < self.alert_cooldown:
                    return  # Skip this alert due to cooldown
            
            # Log the alert
            alert_data = {
                'event_type': 'performance_alert',
                'alert_level': alert.level,
                'metric': alert.metric,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'message': alert.message,
                'timestamp': alert.timestamp
            }
            
            if alert.level == 'critical':
                self.logger.critical(f"Performance alert: {alert_data}")
            else:
                self.logger.warning(f"Performance alert: {alert_data}")
            
            # Update last alert time
            self.last_alert_times[alert_key] = current_time
            
            # Call alert callback if provided
            if self.alert_callback:
                try:
                    self.alert_callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error handling performance alert: {e}")
    
    def log_significant_system_event(self, event_description: str, event_data: Dict[str, Any] = None) -> None:
        """Log a significant system event with current performance context"""
        try:
            # Collect current metrics for context
            metrics = self.performance_monitor.collect_system_metrics()
            
            event_log = {
                'event_type': 'significant_system_event',
                'description': event_description,
                'event_data': event_data or {},
                'performance_context': {
                    'cpu_percent': metrics.cpu.percent,
                    'memory_percent': metrics.memory.percent,
                    'load_avg': metrics.cpu.load_avg_1min,
                    'disk_usage_percent': metrics.disk.usage_percent,
                    'network_activity': {
                        'bytes_sent_per_sec': metrics.network.bytes_sent_per_sec,
                        'bytes_recv_per_sec': metrics.network.bytes_recv_per_sec
                    }
                },
                'timestamp': time.time()
            }
            
            self.logger.info(f"System event with performance context: {event_log}")
            
        except Exception as e:
            self.logger.error(f"Error logging significant system event: {e}")
    
    def _periodic_logging_loop(self) -> None:
        """Background loop for periodic performance metric logging"""
        while self.integration_active:
            try:
                self.log_performance_metrics()
                time.sleep(self.periodic_logging_interval)
            except Exception as e:
                self.logger.error(f"Error in periodic logging loop: {e}")
                time.sleep(self.periodic_logging_interval)
    
    def start_periodic_logging(self) -> None:
        """Start periodic performance metric logging"""
        if not self.integration_active:
            self.integration_active = True
            self.periodic_logging_thread = threading.Thread(
                target=self._periodic_logging_loop,
                daemon=True,
                name="PerformanceLogging"
            )
            self.periodic_logging_thread.start()
            self.logger.info(f"Started periodic performance logging (interval: {self.periodic_logging_interval}s)")
    
    def stop_periodic_logging(self) -> None:
        """Stop periodic performance metric logging"""
        if self.integration_active:
            self.integration_active = False
            if self.periodic_logging_thread and self.periodic_logging_thread.is_alive():
                self.periodic_logging_thread.join(timeout=5.0)
            self.logger.info("Stopped periodic performance logging")
    
    def configure_performance_aware_sampling(self, 
                                           enabled: bool = True,
                                           base_rate: float = 1.0,
                                           load_threshold: float = 80.0) -> None:
        """Configure performance-aware log sampling"""
        self.sampling_adjustment_enabled = enabled
        self.base_sampling_rate = base_rate
        self.load_threshold_for_sampling = load_threshold
        
        self.logger.info(f"Performance-aware sampling configured: enabled={enabled}, "
                        f"base_rate={base_rate}, load_threshold={load_threshold}%")
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance integration statistics"""
        try:
            metrics_history = self.performance_monitor.get_metrics_history(duration_seconds=3600)  # Last hour
            
            if not metrics_history:
                return {'error': 'No metrics history available'}
            
            # Calculate statistics
            cpu_values = [m.cpu.percent for m in metrics_history]
            memory_values = [m.memory.percent for m in metrics_history]
            load_values = [m.cpu.load_avg_1min for m in metrics_history]
            
            return {
                'metrics_count': len(metrics_history),
                'time_range_hours': 1.0,
                'cpu_stats': {
                    'avg': sum(cpu_values) / len(cpu_values),
                    'min': min(cpu_values),
                    'max': max(cpu_values)
                },
                'memory_stats': {
                    'avg': sum(memory_values) / len(memory_values),
                    'min': min(memory_values),
                    'max': max(memory_values)
                },
                'load_stats': {
                    'avg': sum(load_values) / len(load_values),
                    'min': min(load_values),
                    'max': max(load_values)
                },
                'current_sampling_rate': self.get_performance_aware_sampling_rate(),
                'alert_cooldowns_active': len(self.last_alert_times)
            }
        except Exception as e:
            self.logger.error(f"Error getting performance statistics: {e}")
            return {'error': str(e)}


class PerformanceAwareLogger:
    """Logger wrapper that integrates performance monitoring"""
    
    def __init__(self, 
                 base_logger: logging.Logger,
                 performance_integration: PerformanceLoggingIntegration):
        """
        Initialize performance-aware logger
        
        Args:
            base_logger: The base logger to wrap
            performance_integration: Performance integration instance
        """
        self.base_logger = base_logger
        self.performance_integration = performance_integration
    
    def _log_with_performance_context(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log a message with performance context"""
        try:
            # Check if we should sample this log based on performance
            level_name = logging.getLevelName(level)
            if not self.performance_integration.should_sample_based_on_performance(level_name):
                return  # Skip this log due to performance-based sampling
            
            # Create log entry with performance context
            log_entry = {
                'message': msg,
                'level': level_name,
                'args': args,
                'kwargs': kwargs
            }
            
            # Add performance context
            log_entry = self.performance_integration.add_performance_context_to_log_entry(log_entry)
            
            # Log with the base logger
            self.base_logger.log(level, f"{msg} | Performance: {log_entry.get('performance_context', {})}", *args, **kwargs)
            
        except Exception as e:
            # Fallback to basic logging if performance integration fails
            self.base_logger.log(level, msg, *args, **kwargs)
            self.base_logger.error(f"Performance integration error: {e}")
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message with performance context"""
        self._log_with_performance_context(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message with performance context"""
        self._log_with_performance_context(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message with performance context"""
        self._log_with_performance_context(logging.WARNING, msg, *args, **kwargs)
    
    def warn(self, msg: str, *args, **kwargs) -> None:
        """Alias for warning method"""
        self.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message with performance context"""
        self._log_with_performance_context(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message with performance context"""
        self._log_with_performance_context(logging.CRITICAL, msg, *args, **kwargs)