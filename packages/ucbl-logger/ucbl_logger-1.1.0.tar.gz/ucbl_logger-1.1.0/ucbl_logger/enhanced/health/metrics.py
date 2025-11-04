"""
Health metrics collection and alerting for logging system monitoring
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Health alert data structure"""
    severity: AlertSeverity
    message: str
    component: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'severity': self.severity.value,
            'message': self.message,
            'component': self.component,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric point to dictionary"""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp,
            'labels': self.labels
        }


class HealthMetricsCollector:
    """Collects and manages health metrics for the logging system"""
    
    def __init__(self, max_history: int = 1000, retention_seconds: int = 3600):
        self.max_history = max_history
        self.retention_seconds = retention_seconds
        self.metrics_history: deque = deque(maxlen=max_history)
        self.current_metrics: Dict[str, float] = {}
        self.metric_callbacks: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self) -> None:
        """Initialize default logging system metrics"""
        self.register_metric_callback("uptime_seconds", self._get_uptime)
        self.register_metric_callback("memory_usage_mb", self._get_memory_usage)
        self.register_metric_callback("thread_count", self._get_thread_count)
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - getattr(self, '_start_time', time.time())
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0
        except Exception:
            return -1.0  # Error indicator
    
    def _get_thread_count(self) -> float:
        """Get current thread count"""
        return float(threading.active_count())
    
    def register_metric_callback(self, metric_name: str, callback: Callable) -> None:
        """Register a callback function to collect a specific metric"""
        with self._lock:
            self.metric_callbacks[metric_name] = callback
    
    def collect_metrics(self) -> Dict[str, float]:
        """Collect all registered metrics"""
        with self._lock:
            metrics = {}
            
            for name, callback in self.metric_callbacks.items():
                try:
                    value = callback()
                    metrics[name] = float(value)
                    
                    # Store metric point in history
                    metric_point = MetricPoint(name=name, value=value)
                    self.metrics_history.append(metric_point)
                    
                except Exception:
                    # Use last known value or 0 if callback fails
                    metrics[name] = self.current_metrics.get(name, 0.0)
            
            self.current_metrics = metrics
            self._cleanup_old_metrics()
            return metrics.copy()
    
    def _cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period"""
        cutoff_time = time.time() - self.retention_seconds
        
        # Remove old metrics from history
        while (self.metrics_history and 
               self.metrics_history[0].timestamp < cutoff_time):
            self.metrics_history.popleft()
    
    def get_metric_history(self, metric_name: str, 
                          duration_seconds: int = 300) -> List[MetricPoint]:
        """Get historical data for a specific metric"""
        with self._lock:
            cutoff_time = time.time() - duration_seconds
            
            return [
                point for point in self.metrics_history
                if point.name == metric_name and point.timestamp >= cutoff_time
            ]
    
    def get_metric_statistics(self, metric_name: str, 
                            duration_seconds: int = 300) -> Dict[str, float]:
        """Get statistical summary for a metric over time period"""
        history = self.get_metric_history(metric_name, duration_seconds)
        
        if not history:
            return {}
        
        values = [point.value for point in history]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'current': values[-1] if values else 0.0
        }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        with self._lock:
            lines = []
            
            for name, value in self.current_metrics.items():
                # Convert metric name to Prometheus format
                prom_name = f"ucbl_logger_{name.replace('.', '_')}"
                lines.append(f"# TYPE {prom_name} gauge")
                lines.append(f"{prom_name} {value}")
            
            return "\n".join(lines)


class HealthAlerting:
    """Health alerting system for logging components"""
    
    def __init__(self, max_alerts: int = 100):
        self.max_alerts = max_alerts
        self.active_alerts: List[Alert] = []
        self.alert_history: deque = deque(maxlen=max_alerts)
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[Callable] = []
        self._lock = threading.RLock()
    
    def add_alert_rule(self, name: str, condition: Callable, 
                      severity: AlertSeverity, message: str,
                      component: str = "logging_system") -> None:
        """
        Add an alert rule
        
        Args:
            name: Unique name for the alert rule
            condition: Function that returns True when alert should fire
            severity: Alert severity level
            message: Alert message template
            component: Component name that generates the alert
        """
        with self._lock:
            self.alert_rules[name] = {
                'condition': condition,
                'severity': severity,
                'message': message,
                'component': component,
                'last_fired': 0,
                'cooldown_seconds': 300  # 5 minute cooldown
            }
    
    def check_alert_rules(self, metrics: Dict[str, float]) -> List[Alert]:
        """Check all alert rules against current metrics"""
        with self._lock:
            new_alerts = []
            current_time = time.time()
            
            for rule_name, rule in self.alert_rules.items():
                try:
                    # Check cooldown period
                    if (current_time - rule['last_fired']) < rule['cooldown_seconds']:
                        continue
                    
                    # Evaluate condition
                    if rule['condition'](metrics):
                        alert = Alert(
                            severity=rule['severity'],
                            message=rule['message'],
                            component=rule['component'],
                            metadata={'rule_name': rule_name, 'metrics': metrics}
                        )
                        
                        new_alerts.append(alert)
                        self.alert_history.append(alert)
                        rule['last_fired'] = current_time
                        
                        # Notify alert callbacks
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception:
                                pass  # Don't let callback failures break alerting
                
                except Exception:
                    # Log rule evaluation failure but continue
                    pass
            
            # Update active alerts (remove resolved ones, add new ones)
            self._update_active_alerts(new_alerts)
            
            return new_alerts
    
    def _update_active_alerts(self, new_alerts: List[Alert]) -> None:
        """Update the list of active alerts"""
        # For now, just add new alerts and keep a simple list
        # In a more sophisticated system, you'd track alert resolution
        self.active_alerts.extend(new_alerts)
        
        # Keep only recent active alerts (last hour)
        cutoff_time = time.time() - 3600
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp >= cutoff_time
        ]
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register a callback to be notified when alerts fire"""
        with self._lock:
            self.alert_callbacks.append(callback)
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get currently active alerts, optionally filtered by severity"""
        with self._lock:
            if severity:
                return [alert for alert in self.active_alerts if alert.severity == severity]
            return self.active_alerts.copy()
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert status"""
        with self._lock:
            severity_counts = defaultdict(int)
            for alert in self.active_alerts:
                severity_counts[alert.severity.value] += 1
            
            return {
                'total_active': len(self.active_alerts),
                'by_severity': dict(severity_counts),
                'total_rules': len(self.alert_rules),
                'recent_alerts': len([
                    alert for alert in self.alert_history
                    if alert.timestamp >= time.time() - 3600
                ])
            }


class IntegratedHealthMetrics:
    """Integrated health metrics and alerting system"""
    
    def __init__(self, health_monitor=None):
        self.health_monitor = health_monitor
        self.metrics_collector = HealthMetricsCollector()
        self.alerting = HealthAlerting()
        self._setup_default_alerts()
        
        # Set start time for uptime calculation
        self.metrics_collector._start_time = time.time()
    
    def _setup_default_alerts(self) -> None:
        """Setup default alert rules for logging system"""
        
        # High memory usage alert
        self.alerting.add_alert_rule(
            name="high_memory_usage",
            condition=lambda m: m.get('memory_usage_mb', 0) > 500,  # 500MB threshold
            severity=AlertSeverity.WARNING,
            message="High memory usage detected: {memory_usage_mb:.1f}MB",
            component="system_resources"
        )
        
        # Critical memory usage alert
        self.alerting.add_alert_rule(
            name="critical_memory_usage",
            condition=lambda m: m.get('memory_usage_mb', 0) > 1000,  # 1GB threshold
            severity=AlertSeverity.CRITICAL,
            message="Critical memory usage detected: {memory_usage_mb:.1f}MB",
            component="system_resources"
        )
        
        # High thread count alert
        self.alerting.add_alert_rule(
            name="high_thread_count",
            condition=lambda m: m.get('thread_count', 0) > 50,
            severity=AlertSeverity.WARNING,
            message="High thread count detected: {thread_count} threads",
            component="system_resources"
        )
    
    def collect_and_check(self) -> Dict[str, Any]:
        """Collect metrics and check alert rules"""
        metrics = self.metrics_collector.collect_metrics()
        alerts = self.alerting.check_alert_rules(metrics)
        
        return {
            'metrics': metrics,
            'new_alerts': [alert.to_dict() for alert in alerts],
            'alert_summary': self.alerting.get_alert_summary()
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for monitoring dashboards"""
        metrics = self.metrics_collector.current_metrics
        
        return {
            'current_metrics': metrics,
            'metric_statistics': {
                name: self.metrics_collector.get_metric_statistics(name)
                for name in metrics.keys()
            },
            'active_alerts': [alert.to_dict() for alert in self.alerting.get_active_alerts()],
            'alert_summary': self.alerting.get_alert_summary(),
            'health_status': (
                self.health_monitor.get_health_status().state.value
                if self.health_monitor else 'unknown'
            )
        }
    
    def register_buffer_metrics(self, buffer_manager) -> None:
        """Register buffer-specific metrics"""
        def get_buffer_usage():
            try:
                stats = buffer_manager.get_buffer_statistics()
                return stats.get('usage_percentage', 0) * 100
            except Exception:
                return 0.0
        
        def get_buffer_size():
            try:
                stats = buffer_manager.get_buffer_statistics()
                return float(stats.get('current_size', 0))
            except Exception:
                return 0.0
        
        self.metrics_collector.register_metric_callback("buffer_usage_percent", get_buffer_usage)
        self.metrics_collector.register_metric_callback("buffer_current_size", get_buffer_size)
        
        # Add buffer-specific alerts
        self.alerting.add_alert_rule(
            name="buffer_high_usage",
            condition=lambda m: m.get('buffer_usage_percent', 0) > 80,
            severity=AlertSeverity.WARNING,
            message="Buffer usage high: {buffer_usage_percent:.1f}%",
            component="buffer_manager"
        )
        
        self.alerting.add_alert_rule(
            name="buffer_critical_usage",
            condition=lambda m: m.get('buffer_usage_percent', 0) > 95,
            severity=AlertSeverity.CRITICAL,
            message="Buffer usage critical: {buffer_usage_percent:.1f}%",
            component="buffer_manager"
        )
    
    def register_delivery_metrics(self, delivery_manager) -> None:
        """Register delivery-specific metrics"""
        def get_delivery_success_rate():
            try:
                if hasattr(delivery_manager, 'get_delivery_statistics'):
                    stats = delivery_manager.get_delivery_statistics()
                    return (1.0 - stats.get('failure_rate', 0)) * 100
                return 100.0
            except Exception:
                return 0.0
        
        self.metrics_collector.register_metric_callback("delivery_success_rate", get_delivery_success_rate)
        
        # Add delivery-specific alerts
        self.alerting.add_alert_rule(
            name="low_delivery_success_rate",
            condition=lambda m: m.get('delivery_success_rate', 100) < 90,
            severity=AlertSeverity.WARNING,
            message="Low delivery success rate: {delivery_success_rate:.1f}%",
            component="delivery_manager"
        )