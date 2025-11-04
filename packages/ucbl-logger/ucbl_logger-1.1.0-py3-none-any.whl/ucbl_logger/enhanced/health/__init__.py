"""
Health monitoring components for enhanced EKS logging
"""

from .interfaces import IHealthMonitor
from .models import HealthStatus, HealthState
from .base import BaseHealthMonitor, HealthMonitor
from .endpoint import HealthEndpoint, create_flask_health_routes, create_fastapi_health_routes
from .integration import (
    HealthIntegration, 
    KubernetesHealthIntegration,
    integrate_with_flask_app,
    integrate_with_fastapi_app,
    create_middleware_health_check
)

# Import metrics components
try:
    from .metrics import (
        HealthMetricsCollector, 
        HealthAlerting, 
        IntegratedHealthMetrics,
        Alert,
        AlertSeverity,
        MetricPoint
    )
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False

__all__ = [
    'IHealthMonitor', 
    'HealthStatus', 
    'HealthState', 
    'BaseHealthMonitor', 
    'HealthMonitor',
    'HealthEndpoint',
    'create_flask_health_routes',
    'create_fastapi_health_routes',
    'HealthIntegration',
    'KubernetesHealthIntegration',
    'integrate_with_flask_app',
    'integrate_with_fastapi_app',
    'create_middleware_health_check'
]

if _METRICS_AVAILABLE:
    __all__.extend([
        'HealthMetricsCollector',
        'HealthAlerting',
        'IntegratedHealthMetrics',
        'Alert',
        'AlertSeverity',
        'MetricPoint'
    ])