"""
Data models for health monitoring
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum
import time


class HealthState(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthStatus:
    """Health status of logging system"""
    state: HealthState
    timestamp: float = field(default_factory=time.time)
    components: Dict[str, bool] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    uptime_seconds: float = 0.0
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self.state == HealthState.HEALTHY
    
    def add_component_status(self, name: str, healthy: bool) -> None:
        """Add component health status"""
        self.components[name] = healthy
        if not healthy and self.state == HealthState.HEALTHY:
            self.state = HealthState.DEGRADED
    
    def add_alert(self, message: str) -> None:
        """Add health alert"""
        self.alerts.append(message)
        if self.state == HealthState.HEALTHY:
            self.state = HealthState.DEGRADED