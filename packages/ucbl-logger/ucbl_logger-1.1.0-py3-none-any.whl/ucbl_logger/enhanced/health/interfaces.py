"""
Interfaces for health monitoring components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import HealthStatus


class IHealthMonitor(ABC):
    """Interface for logging system health monitoring"""
    
    @abstractmethod
    def get_health_status(self) -> HealthStatus:
        """Get current health status of the logging system"""
        pass
    
    @abstractmethod
    def check_component_health(self, component_name: str) -> bool:
        """Check health of a specific logging component"""
        pass
    
    @abstractmethod
    def register_health_check(self, name: str, check_function: callable) -> None:
        """Register a custom health check function"""
        pass
    
    @abstractmethod
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get detailed health metrics for monitoring"""
        pass
    
    @abstractmethod
    def is_degraded(self) -> bool:
        """Check if logging system is in degraded state"""
        pass