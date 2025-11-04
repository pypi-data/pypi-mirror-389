"""
Health check endpoint implementation for HTTP-based health monitoring
"""

import json
from typing import Dict, Any, Optional, Callable
from .base import HealthMonitor
from .models import HealthState


class HealthEndpoint:
    """HTTP health check endpoint for logging system health monitoring"""
    
    def __init__(self, health_monitor: HealthMonitor):
        self.health_monitor = health_monitor
        self.custom_checks: Dict[str, Callable] = {}
    
    def health_check_handler(self, request_path: str = "/health") -> Dict[str, Any]:
        """
        Main health check handler that returns comprehensive health status
        
        Args:
            request_path: The request path to determine response format
            
        Returns:
            Dictionary containing health status information
        """
        status = self.health_monitor.get_health_status()
        
        response = {
            'status': status.state.value,
            'timestamp': status.timestamp,
            'uptime_seconds': status.uptime_seconds,
            'components': status.components,
            'metrics': status.metrics
        }
        
        if status.alerts:
            response['alerts'] = status.alerts
        
        return response
    
    def liveness_probe_handler(self) -> Dict[str, Any]:
        """
        Kubernetes liveness probe handler
        
        Returns:
            Simple status for liveness check
        """
        is_alive = self.health_monitor.get_liveness_status()
        
        return {
            'status': 'alive' if is_alive else 'dead',
            'timestamp': self.health_monitor.get_health_status().timestamp
        }
    
    def readiness_probe_handler(self) -> Dict[str, Any]:
        """
        Kubernetes readiness probe handler
        
        Returns:
            Simple status for readiness check
        """
        is_ready = self.health_monitor.get_readiness_status()
        status = self.health_monitor.get_health_status()
        
        response = {
            'status': 'ready' if is_ready else 'not_ready',
            'timestamp': status.timestamp,
            'state': status.state.value
        }
        
        # Include component status for debugging
        if not is_ready:
            response['components'] = status.components
            if status.alerts:
                response['alerts'] = status.alerts
        
        return response
    
    def metrics_handler(self) -> Dict[str, Any]:
        """
        Detailed metrics handler for monitoring systems
        
        Returns:
            Comprehensive metrics for external monitoring
        """
        status = self.health_monitor.get_health_status()
        metrics = self.health_monitor.get_health_metrics()
        
        return {
            'health': {
                'state': status.state.value,
                'uptime_seconds': status.uptime_seconds,
                'component_count': len(status.components),
                'healthy_components': sum(1 for healthy in status.components.values() if healthy)
            },
            'components': status.components,
            'metrics': status.metrics,
            'alerts': status.alerts
        }
    
    def register_custom_check(self, name: str, check_function: Callable) -> None:
        """
        Register a custom health check
        
        Args:
            name: Name of the health check
            check_function: Function that returns boolean health status
        """
        self.custom_checks[name] = check_function
        self.health_monitor.register_health_check(name, check_function)
    
    def get_http_status_code(self, health_status: Optional[Dict[str, Any]] = None) -> int:
        """
        Get appropriate HTTP status code based on health status
        
        Args:
            health_status: Optional health status dict, will fetch if not provided
            
        Returns:
            HTTP status code (200, 503, etc.)
        """
        if health_status is None:
            health_status = self.health_check_handler()
        
        status = health_status.get('status', 'unknown')
        
        if status == HealthState.HEALTHY.value:
            return 200  # OK
        elif status == HealthState.DEGRADED.value:
            return 200  # Still OK, but with warnings
        elif status == HealthState.UNHEALTHY.value:
            return 503  # Service Unavailable
        else:
            return 503  # Unknown status, assume unhealthy
    
    def format_response_for_framework(self, response_data: Dict[str, Any], 
                                    framework: str = "flask") -> Any:
        """
        Format response for specific web framework
        
        Args:
            response_data: Health check response data
            framework: Web framework type ("flask", "fastapi", "django")
            
        Returns:
            Framework-specific response object
        """
        status_code = self.get_http_status_code(response_data)
        
        if framework.lower() == "flask":
            try:
                from flask import jsonify, Response
                return jsonify(response_data), status_code
            except ImportError:
                pass
        
        elif framework.lower() == "fastapi":
            try:
                from fastapi import Response
                return Response(
                    content=json.dumps(response_data),
                    status_code=status_code,
                    media_type="application/json"
                )
            except ImportError:
                pass
        
        elif framework.lower() == "django":
            try:
                from django.http import JsonResponse
                return JsonResponse(response_data, status=status_code)
            except ImportError:
                pass
        
        # Fallback to plain dict with status code
        return response_data, status_code


def create_flask_health_routes(app, health_monitor: HealthMonitor, 
                             base_path: str = "/health") -> None:
    """
    Create Flask routes for health monitoring
    
    Args:
        app: Flask application instance
        health_monitor: HealthMonitor instance
        base_path: Base path for health endpoints
    """
    try:
        from flask import jsonify
        
        endpoint = HealthEndpoint(health_monitor)
        
        @app.route(f"{base_path}")
        def health_check():
            response_data = endpoint.health_check_handler()
            status_code = endpoint.get_http_status_code(response_data)
            return jsonify(response_data), status_code
        
        @app.route(f"{base_path}/live")
        def liveness_probe():
            response_data = endpoint.liveness_probe_handler()
            status_code = 200 if response_data['status'] == 'alive' else 503
            return jsonify(response_data), status_code
        
        @app.route(f"{base_path}/ready")
        def readiness_probe():
            response_data = endpoint.readiness_probe_handler()
            status_code = 200 if response_data['status'] == 'ready' else 503
            return jsonify(response_data), status_code
        
        @app.route(f"{base_path}/metrics")
        def health_metrics():
            response_data = endpoint.metrics_handler()
            return jsonify(response_data), 200
            
    except ImportError:
        raise ImportError("Flask is required to create Flask health routes")


def create_fastapi_health_routes(app, health_monitor: HealthMonitor, 
                               base_path: str = "/health") -> None:
    """
    Create FastAPI routes for health monitoring
    
    Args:
        app: FastAPI application instance
        health_monitor: HealthMonitor instance
        base_path: Base path for health endpoints
    """
    try:
        from fastapi import Response
        
        endpoint = HealthEndpoint(health_monitor)
        
        @app.get(f"{base_path}")
        async def health_check():
            response_data = endpoint.health_check_handler()
            status_code = endpoint.get_http_status_code(response_data)
            return Response(
                content=json.dumps(response_data),
                status_code=status_code,
                media_type="application/json"
            )
        
        @app.get(f"{base_path}/live")
        async def liveness_probe():
            response_data = endpoint.liveness_probe_handler()
            status_code = 200 if response_data['status'] == 'alive' else 503
            return Response(
                content=json.dumps(response_data),
                status_code=status_code,
                media_type="application/json"
            )
        
        @app.get(f"{base_path}/ready")
        async def readiness_probe():
            response_data = endpoint.readiness_probe_handler()
            status_code = 200 if response_data['status'] == 'ready' else 503
            return Response(
                content=json.dumps(response_data),
                status_code=status_code,
                media_type="application/json"
            )
        
        @app.get(f"{base_path}/metrics")
        async def health_metrics():
            response_data = endpoint.metrics_handler()
            return Response(
                content=json.dumps(response_data),
                status_code=200,
                media_type="application/json"
            )
            
    except ImportError:
        raise ImportError("FastAPI is required to create FastAPI health routes")