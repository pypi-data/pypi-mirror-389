"""
Integration utilities for health monitoring with existing application health endpoints
"""

import json
from typing import Dict, Any, Optional, Callable, Union
from .base import HealthMonitor
from .models import HealthState


class HealthIntegration:
    """Integration helper for adding logging health to existing application health checks"""
    
    def __init__(self, health_monitor: HealthMonitor, 
                 include_detailed_metrics: bool = True):
        self.health_monitor = health_monitor
        self.include_detailed_metrics = include_detailed_metrics
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of logging system health for integration"""
        status = self.health_monitor.get_health_status()
        
        summary = {
            'logging_system': {
                'status': status.state.value,
                'healthy': status.is_healthy(),
                'uptime_seconds': status.uptime_seconds,
                'component_count': len(status.components),
                'healthy_components': sum(1 for healthy in status.components.values() if healthy)
            }
        }
        
        if status.alerts:
            summary['logging_system']['alerts'] = status.alerts
        
        if self.include_detailed_metrics and status.metrics:
            summary['logging_system']['metrics'] = status.metrics
        
        return summary
    
    def merge_with_app_health(self, app_health: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge logging system health with existing application health data
        
        Args:
            app_health: Existing application health data
            
        Returns:
            Combined health data with logging system information
        """
        logging_health = self.get_health_summary()
        
        # Create a copy to avoid modifying the original
        combined_health = app_health.copy()
        
        # Add logging system health
        combined_health.update(logging_health)
        
        # Update overall status if logging system is unhealthy
        logging_status = logging_health['logging_system']['status']
        if logging_status == HealthState.UNHEALTHY.value:
            # If app was healthy but logging is unhealthy, mark as degraded
            if combined_health.get('status') == 'healthy':
                combined_health['status'] = 'degraded'
                combined_health.setdefault('issues', []).append(
                    'Logging system is unhealthy'
                )
        elif logging_status == HealthState.DEGRADED.value:
            # If app was healthy but logging is degraded, mark as degraded
            if combined_health.get('status') == 'healthy':
                combined_health['status'] = 'degraded'
                combined_health.setdefault('warnings', []).append(
                    'Logging system is degraded'
                )
        
        return combined_health
    
    def create_health_check_wrapper(self, original_health_check: Callable) -> Callable:
        """
        Create a wrapper around an existing health check function
        
        Args:
            original_health_check: Original health check function
            
        Returns:
            Wrapped health check function that includes logging system health
        """
        def wrapped_health_check(*args, **kwargs):
            # Get original health check result
            try:
                app_health = original_health_check(*args, **kwargs)
                
                # Handle different return types
                if isinstance(app_health, dict):
                    return self.merge_with_app_health(app_health)
                elif isinstance(app_health, tuple) and len(app_health) == 2:
                    # Assume (data, status_code) tuple
                    data, status_code = app_health
                    if isinstance(data, dict):
                        merged_data = self.merge_with_app_health(data)
                        # Adjust status code if logging system is unhealthy
                        logging_status = self.health_monitor.get_health_status()
                        if (logging_status.state == HealthState.UNHEALTHY and 
                            status_code == 200):
                            status_code = 503
                        return merged_data, status_code
                    return app_health
                else:
                    # Unknown return type, return as-is
                    return app_health
                    
            except Exception:
                # If original health check fails, still provide logging health
                logging_health = self.get_health_summary()
                logging_health['application'] = {'status': 'error', 'message': 'Health check failed'}
                return logging_health
        
        return wrapped_health_check


class KubernetesHealthIntegration:
    """Kubernetes-specific health integration utilities"""
    
    def __init__(self, health_monitor: HealthMonitor):
        self.health_monitor = health_monitor
    
    def create_liveness_probe(self) -> Callable:
        """Create a liveness probe function for Kubernetes"""
        def liveness_probe():
            is_alive = self.health_monitor.get_liveness_status()
            
            if is_alive:
                return {'status': 'alive'}, 200
            else:
                return {'status': 'dead', 'reason': 'logging_system_unhealthy'}, 503
        
        return liveness_probe
    
    def create_readiness_probe(self) -> Callable:
        """Create a readiness probe function for Kubernetes"""
        def readiness_probe():
            is_ready = self.health_monitor.get_readiness_status()
            status = self.health_monitor.get_health_status()
            
            response = {
                'status': 'ready' if is_ready else 'not_ready',
                'logging_system_state': status.state.value
            }
            
            if not is_ready:
                response['components'] = status.components
                if status.alerts:
                    response['alerts'] = status.alerts
            
            status_code = 200 if is_ready else 503
            return response, status_code
        
        return readiness_probe
    
    def create_startup_probe(self, startup_timeout_seconds: int = 30) -> Callable:
        """Create a startup probe function for Kubernetes"""
        import time
        start_time = time.time()
        
        def startup_probe():
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Check if we're past the startup timeout
            if elapsed > startup_timeout_seconds:
                return {'status': 'timeout', 'elapsed_seconds': elapsed}, 503
            
            # Check if logging system is ready
            is_ready = self.health_monitor.get_readiness_status()
            
            if is_ready:
                return {
                    'status': 'started',
                    'elapsed_seconds': elapsed,
                    'logging_system_ready': True
                }, 200
            else:
                return {
                    'status': 'starting',
                    'elapsed_seconds': elapsed,
                    'logging_system_ready': False
                }, 503
        
        return startup_probe


def create_middleware_health_check(health_monitor: HealthMonitor, 
                                 path: str = "/health/logging") -> Callable:
    """
    Create middleware function for web frameworks to add logging health endpoint
    
    Args:
        health_monitor: HealthMonitor instance
        path: URL path for the health endpoint
        
    Returns:
        Middleware function
    """
    integration = HealthIntegration(health_monitor)
    
    def middleware(request, response_handler):
        # Check if this is a health check request
        if hasattr(request, 'path') and request.path == path:
            health_data = integration.get_health_summary()
            status = health_monitor.get_health_status()
            
            status_code = 200
            if status.state == HealthState.UNHEALTHY:
                status_code = 503
            elif status.state == HealthState.DEGRADED:
                status_code = 200  # Still operational
            
            # Return health response (format depends on framework)
            return {
                'data': health_data,
                'status_code': status_code,
                'content_type': 'application/json'
            }
        
        # Not a health check request, continue with normal processing
        return response_handler(request)
    
    return middleware


def integrate_with_flask_app(app, health_monitor: HealthMonitor, 
                           base_path: str = "/health") -> None:
    """
    Integrate health monitoring with a Flask application
    
    Args:
        app: Flask application instance
        health_monitor: HealthMonitor instance
        base_path: Base path for health endpoints
    """
    try:
        from flask import jsonify
        from .endpoint import create_flask_health_routes
        
        # Create standard health routes
        create_flask_health_routes(app, health_monitor, base_path)
        
        # Add integration-specific routes
        integration = HealthIntegration(health_monitor)
        k8s_integration = KubernetesHealthIntegration(health_monitor)
        
        @app.route(f"{base_path}/summary")
        def health_summary():
            data = integration.get_health_summary()
            return jsonify(data), 200
        
        @app.route(f"{base_path}/k8s/startup")
        def k8s_startup_probe():
            probe = k8s_integration.create_startup_probe()
            data, status_code = probe()
            return jsonify(data), status_code
            
    except ImportError:
        raise ImportError("Flask is required for Flask integration")


def integrate_with_fastapi_app(app, health_monitor: HealthMonitor, 
                             base_path: str = "/health") -> None:
    """
    Integrate health monitoring with a FastAPI application
    
    Args:
        app: FastAPI application instance
        health_monitor: HealthMonitor instance
        base_path: Base path for health endpoints
    """
    try:
        from fastapi import Response
        from .endpoint import create_fastapi_health_routes
        
        # Create standard health routes
        create_fastapi_health_routes(app, health_monitor, base_path)
        
        # Add integration-specific routes
        integration = HealthIntegration(health_monitor)
        k8s_integration = KubernetesHealthIntegration(health_monitor)
        
        @app.get(f"{base_path}/summary")
        async def health_summary():
            data = integration.get_health_summary()
            return Response(
                content=json.dumps(data),
                status_code=200,
                media_type="application/json"
            )
        
        @app.get(f"{base_path}/k8s/startup")
        async def k8s_startup_probe():
            probe = k8s_integration.create_startup_probe()
            data, status_code = probe()
            return Response(
                content=json.dumps(data),
                status_code=status_code,
                media_type="application/json"
            )
            
    except ImportError:
        raise ImportError("FastAPI is required for FastAPI integration")