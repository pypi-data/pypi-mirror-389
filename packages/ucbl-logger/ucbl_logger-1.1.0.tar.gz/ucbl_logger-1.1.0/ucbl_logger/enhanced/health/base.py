"""
Base implementation for health monitoring components
"""

import time
import threading
from typing import Dict, Any, Callable, Optional
from .interfaces import IHealthMonitor
from .models import HealthStatus, HealthState


class BaseHealthMonitor(IHealthMonitor):
    """Base implementation of health monitor"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_checks: Dict[str, Callable] = {}
        self.component_status: Dict[str, bool] = {}
        self._lock = threading.RLock()
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status of the logging system"""
        with self._lock:
            # Run all registered health checks
            for name, check_func in self.health_checks.items():
                try:
                    self.component_status[name] = check_func()
                except Exception:
                    self.component_status[name] = False
            
            # Determine overall health state
            if not self.component_status:
                state = HealthState.UNKNOWN
            elif all(self.component_status.values()):
                state = HealthState.HEALTHY
            elif any(self.component_status.values()):
                state = HealthState.DEGRADED
            else:
                state = HealthState.UNHEALTHY
            
            return HealthStatus(
                state=state,
                timestamp=time.time(),
                components=self.component_status.copy(),
                uptime_seconds=time.time() - self.start_time
            )
    
    def check_component_health(self, component_name: str) -> bool:
        """Check health of a specific logging component"""
        with self._lock:
            if component_name in self.health_checks:
                try:
                    return self.health_checks[component_name]()
                except Exception:
                    return False
            return self.component_status.get(component_name, True)
    
    def register_health_check(self, name: str, check_function: Callable) -> None:
        """Register a custom health check function"""
        with self._lock:
            self.health_checks[name] = check_function
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get detailed health metrics for monitoring"""
        with self._lock:
            return {
                'uptime_seconds': time.time() - self.start_time,
                'component_count': len(self.component_status),
                'healthy_components': sum(1 for status in self.component_status.values() if status),
                'registered_checks': list(self.health_checks.keys())
            }
    
    def is_degraded(self) -> bool:
        """Check if logging system is in degraded state"""
        status = self.get_health_status()
        return status.state in [HealthState.DEGRADED, HealthState.UNHEALTHY]


class HealthMonitor(BaseHealthMonitor):
    """Comprehensive health monitor for enhanced EKS logging system"""
    
    def __init__(self, buffer_manager=None, delivery_manager=None, enable_metrics=True):
        super().__init__()
        self.buffer_manager = buffer_manager
        self.delivery_manager = delivery_manager
        self.buffer_threshold_warning = 0.8  # 80% buffer usage warning
        self.buffer_threshold_critical = 0.95  # 95% buffer usage critical
        self.delivery_failure_threshold = 0.1  # 10% delivery failure rate threshold
        
        # Initialize metrics system if enabled
        self.metrics_system = None
        if enable_metrics:
            try:
                from .metrics import IntegratedHealthMetrics
                self.metrics_system = IntegratedHealthMetrics(health_monitor=self)
                
                # Register component-specific metrics
                if buffer_manager:
                    self.metrics_system.register_buffer_metrics(buffer_manager)
                if delivery_manager:
                    self.metrics_system.register_delivery_metrics(delivery_manager)
            except ImportError:
                # Metrics system not available, continue without it
                pass
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        """Register default health checks for logging system components"""
        self.register_health_check("buffer_status", self._check_buffer_health)
        self.register_health_check("delivery_health", self._check_delivery_health)
        self.register_health_check("system_resources", self._check_system_resources)
    
    def _check_buffer_health(self) -> bool:
        """Check buffer health status"""
        if not self.buffer_manager:
            return True  # No buffer manager means no buffer issues
        
        try:
            stats = self.buffer_manager.get_buffer_statistics()
            buffer_usage = stats.get('usage_percentage', 0)
            
            # Check if buffer usage is within acceptable limits
            return buffer_usage < self.buffer_threshold_critical
        except Exception:
            return False
    
    def _check_delivery_health(self) -> bool:
        """Check log delivery health"""
        if not self.delivery_manager:
            return True  # No delivery manager means no delivery issues
        
        try:
            # Check delivery statistics if available
            if hasattr(self.delivery_manager, 'get_delivery_statistics'):
                stats = self.delivery_manager.get_delivery_statistics()
                failure_rate = stats.get('failure_rate', 0)
                return failure_rate < self.delivery_failure_threshold
            
            # Fallback to buffer manager delivery health check
            if self.buffer_manager:
                return self.buffer_manager.is_buffer_healthy()
            
            return True
        except Exception:
            return False
    
    def _check_system_resources(self) -> bool:
        """Check system resource availability"""
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 95:  # 95% memory usage is critical
                return False
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 95:  # 95% disk usage is critical
                return False
            
            return True
        except ImportError:
            # psutil not available, assume healthy
            return True
        except Exception:
            return False
    
    def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status with detailed metrics"""
        status = super().get_health_status()
        
        # Add detailed metrics
        metrics = self.get_health_metrics()
        
        # Collect metrics and check alerts if metrics system is available
        if self.metrics_system:
            try:
                metrics_data = self.metrics_system.collect_and_check()
                metrics.update(metrics_data['metrics'])
                
                # Add new alerts from metrics system
                for alert_dict in metrics_data['new_alerts']:
                    status.add_alert(f"{alert_dict['component']}: {alert_dict['message']}")
                
                # Add alert summary to metrics
                metrics['alert_summary'] = metrics_data['alert_summary']
            except Exception:
                status.add_alert("Failed to collect metrics system data")
        
        # Add buffer metrics if available
        if self.buffer_manager:
            try:
                buffer_stats = self.buffer_manager.get_buffer_statistics()
                metrics['buffer'] = buffer_stats
                
                # Add buffer-specific alerts
                usage = buffer_stats.get('usage_percentage', 0)
                if usage > self.buffer_threshold_critical:
                    status.add_alert(f"Buffer usage critical: {usage:.1f}%")
                elif usage > self.buffer_threshold_warning:
                    status.add_alert(f"Buffer usage warning: {usage:.1f}%")
            except Exception:
                status.add_alert("Failed to retrieve buffer statistics")
        
        # Add delivery metrics if available
        if self.delivery_manager and hasattr(self.delivery_manager, 'get_delivery_statistics'):
            try:
                delivery_stats = self.delivery_manager.get_delivery_statistics()
                metrics['delivery'] = delivery_stats
                
                failure_rate = delivery_stats.get('failure_rate', 0)
                if failure_rate > self.delivery_failure_threshold:
                    status.add_alert(f"High delivery failure rate: {failure_rate:.1%}")
            except Exception:
                status.add_alert("Failed to retrieve delivery statistics")
        
        status.metrics = metrics
        return status
    
    def get_kubernetes_health_endpoint(self) -> Dict[str, Any]:
        """Get health status formatted for Kubernetes health probes"""
        status = self.get_health_status()
        
        return {
            'status': status.state.value,
            'timestamp': status.timestamp,
            'uptime': status.uptime_seconds,
            'components': status.components,
            'alerts': status.alerts
        }
    
    def get_readiness_status(self) -> bool:
        """Get readiness status for Kubernetes readiness probe"""
        status = self.get_health_status()
        # Ready if healthy or degraded (can still process logs)
        return status.state in [HealthState.HEALTHY, HealthState.DEGRADED]
    
    def get_liveness_status(self) -> bool:
        """Get liveness status for Kubernetes liveness probe"""
        status = self.get_health_status()
        # Alive unless completely unhealthy
        return status.state != HealthState.UNHEALTHY
    
    def set_buffer_thresholds(self, warning: float, critical: float) -> None:
        """Set buffer usage thresholds"""
        if 0 <= warning <= critical <= 1:
            self.buffer_threshold_warning = warning
            self.buffer_threshold_critical = critical
    
    def set_delivery_failure_threshold(self, threshold: float) -> None:
        """Set delivery failure rate threshold"""
        if 0 <= threshold <= 1:
            self.delivery_failure_threshold = threshold
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for monitoring systems"""
        if self.metrics_system:
            return self.metrics_system.get_dashboard_data()
        
        # Fallback to basic health status
        status = self.get_health_status()
        return {
            'current_metrics': status.metrics,
            'active_alerts': status.alerts,
            'health_status': status.state.value
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if self.metrics_system:
            return self.metrics_system.metrics_collector.export_prometheus_metrics()
        return ""
    
    def register_custom_metric(self, name: str, callback: Callable) -> None:
        """Register a custom metric collection callback"""
        if self.metrics_system:
            self.metrics_system.metrics_collector.register_metric_callback(name, callback)
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register a callback to be notified when alerts fire"""
        if self.metrics_system:
            self.metrics_system.alerting.register_alert_callback(callback)