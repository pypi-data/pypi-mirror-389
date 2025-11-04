"""
Interfaces for performance monitoring components
"""

from abc import ABC, abstractmethod
from typing import List
from .models import SystemMetrics, PerformanceAlert


class IPerformanceMonitor(ABC):
    """Interface for system performance monitoring"""
    
    @abstractmethod
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        pass
    
    @abstractmethod
    def check_performance_thresholds(self, metrics: SystemMetrics) -> List[PerformanceAlert]:
        """Check if metrics exceed configured thresholds and return alerts"""
        pass
    
    @abstractmethod
    def get_metrics_history(self, duration_seconds: int = 300) -> List[SystemMetrics]:
        """Get historical metrics for specified duration"""
        pass
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """Start background performance monitoring"""
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop background performance monitoring"""
        pass