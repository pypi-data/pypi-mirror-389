"""
Base implementation for performance monitoring components
"""

import time
from typing import List
from .interfaces import IPerformanceMonitor
from .models import SystemMetrics, PerformanceThresholds, PerformanceAlert


class BasePerformanceMonitor(IPerformanceMonitor):
    """Base implementation of performance monitor"""
    
    def __init__(self, thresholds: PerformanceThresholds = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.metrics_history: List[SystemMetrics] = []
        self.monitoring_active = False
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        # Basic implementation - will be enhanced with actual system metrics
        return SystemMetrics(timestamp=time.time())
    
    def check_performance_thresholds(self, metrics: SystemMetrics) -> List[PerformanceAlert]:
        """Check if metrics exceed configured thresholds and return alerts"""
        alerts = []
        
        cpu_alert = self.thresholds.check_cpu_threshold(metrics.cpu.percent)
        if cpu_alert:
            alerts.append(cpu_alert)
        
        memory_alert = self.thresholds.check_memory_threshold(metrics.memory.percent)
        if memory_alert:
            alerts.append(memory_alert)
        
        return alerts
    
    def get_metrics_history(self, duration_seconds: int = 300) -> List[SystemMetrics]:
        """Get historical metrics for specified duration"""
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def start_monitoring(self) -> None:
        """Start background performance monitoring"""
        self.monitoring_active = True
    
    def stop_monitoring(self) -> None:
        """Stop background performance monitoring"""
        self.monitoring_active = False