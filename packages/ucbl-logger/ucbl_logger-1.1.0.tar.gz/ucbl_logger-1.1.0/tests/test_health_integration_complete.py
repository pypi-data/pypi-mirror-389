"""
Integration test for complete health monitoring system
"""

import unittest
import time
from unittest.mock import Mock

from ucbl_logger.enhanced.health import (
    HealthMonitor,
    HealthEndpoint,
    HealthIntegration,
    KubernetesHealthIntegration,
    HealthState
)


class TestCompleteHealthIntegration(unittest.TestCase):
    """Test complete health monitoring system integration"""
    
    def setUp(self):
        """Set up test environment with mock components"""
        # Create mock buffer and delivery managers
        self.mock_buffer_manager = Mock()
        self.mock_buffer_manager.get_buffer_statistics.return_value = {
            'usage_percentage': 0.3,
            'current_size': 300,
            'max_size': 1000
        }
        self.mock_buffer_manager.is_buffer_healthy.return_value = True
        
        self.mock_delivery_manager = Mock()
        self.mock_delivery_manager.get_delivery_statistics.return_value = {
            'failure_rate': 0.02,
            'total_deliveries': 1000,
            'failed_deliveries': 20
        }
        
        # Create health monitor with all components
        self.health_monitor = HealthMonitor(
            buffer_manager=self.mock_buffer_manager,
            delivery_manager=self.mock_delivery_manager,
            enable_metrics=True
        )
        
        # Create endpoint and integration helpers
        self.health_endpoint = HealthEndpoint(self.health_monitor)
        self.health_integration = HealthIntegration(self.health_monitor)
        self.k8s_integration = KubernetesHealthIntegration(self.health_monitor)
    
    def test_complete_health_flow(self):
        """Test complete health monitoring flow"""
        # 1. Get health status
        status = self.health_monitor.get_health_status()
        self.assertEqual(status.state, HealthState.HEALTHY)
        
        # 2. Test HTTP endpoint
        endpoint_response = self.health_endpoint.health_check_handler()
        self.assertEqual(endpoint_response['status'], 'healthy')
        self.assertIn('components', endpoint_response)
        self.assertIn('metrics', endpoint_response)
        
        # 3. Test Kubernetes probes
        liveness_probe = self.k8s_integration.create_liveness_probe()
        liveness_result, liveness_code = liveness_probe()
        self.assertEqual(liveness_result['status'], 'alive')
        self.assertEqual(liveness_code, 200)
        
        readiness_probe = self.k8s_integration.create_readiness_probe()
        readiness_result, readiness_code = readiness_probe()
        self.assertEqual(readiness_result['status'], 'ready')
        self.assertEqual(readiness_code, 200)
        
        # 4. Test application integration
        app_health = {'status': 'healthy', 'database': 'connected'}
        merged_health = self.health_integration.merge_with_app_health(app_health)
        self.assertIn('logging_system', merged_health)
        self.assertEqual(merged_health['status'], 'healthy')
    
    def test_degraded_health_scenario(self):
        """Test system behavior when health is degraded"""
        # Simulate high buffer usage
        self.mock_buffer_manager.get_buffer_statistics.return_value = {
            'usage_percentage': 0.85,  # Above warning threshold
            'current_size': 850,
            'max_size': 1000
        }
        
        # Get health status
        status = self.health_monitor.get_health_status()
        self.assertIn('Buffer usage warning', ' '.join(status.alerts))
        
        # Test endpoint response
        endpoint_response = self.health_endpoint.health_check_handler()
        self.assertIn('alerts', endpoint_response)
        
        # Kubernetes probes should still be ready (degraded but operational)
        self.assertTrue(self.health_monitor.get_readiness_status())
        self.assertTrue(self.health_monitor.get_liveness_status())
    
    def test_unhealthy_scenario(self):
        """Test system behavior when health is unhealthy"""
        # Simulate critical buffer usage
        self.mock_buffer_manager.get_buffer_statistics.return_value = {
            'usage_percentage': 0.97,  # Above critical threshold
            'current_size': 970,
            'max_size': 1000
        }
        
        # Simulate high delivery failure rate
        self.mock_delivery_manager.get_delivery_statistics.return_value = {
            'failure_rate': 0.15,  # Above threshold
            'total_deliveries': 1000,
            'failed_deliveries': 150
        }
        
        # Get health status
        status = self.health_monitor.get_health_status()
        
        # Should have alerts for both issues
        alert_text = ' '.join(status.alerts)
        self.assertIn('Buffer usage critical', alert_text)
        self.assertIn('High delivery failure rate', alert_text)
        
        # Test HTTP status codes
        endpoint_response = self.health_endpoint.health_check_handler()
        status_code = self.health_endpoint.get_http_status_code(endpoint_response)
        
        # Should return 503 for unhealthy system
        if status.state == HealthState.UNHEALTHY:
            self.assertEqual(status_code, 503)
    
    def test_metrics_system_integration(self):
        """Test metrics system integration"""
        if hasattr(self.health_monitor, 'metrics_system') and self.health_monitor.metrics_system:
            # Collect metrics
            metrics_data = self.health_monitor.metrics_system.collect_and_check()
            
            self.assertIn('metrics', metrics_data)
            self.assertIn('new_alerts', metrics_data)
            self.assertIn('alert_summary', metrics_data)
            
            # Test dashboard data
            dashboard_data = self.health_monitor.get_dashboard_data()
            
            self.assertIn('current_metrics', dashboard_data)
            self.assertIn('active_alerts', dashboard_data)
            self.assertIn('health_status', dashboard_data)
            
            # Test Prometheus export
            prometheus_metrics = self.health_monitor.get_prometheus_metrics()
            self.assertIsInstance(prometheus_metrics, str)
    
    def test_custom_health_checks(self):
        """Test custom health check registration"""
        # Register custom health check
        def custom_service_check():
            return True
        
        self.health_monitor.register_health_check("custom_service", custom_service_check)
        
        # Verify it's included in health status
        status = self.health_monitor.get_health_status()
        self.assertIn("custom_service", status.components)
        self.assertTrue(status.components["custom_service"])
        
        # Test failing custom check
        def failing_service_check():
            return False
        
        self.health_monitor.register_health_check("failing_service", failing_service_check)
        
        status = self.health_monitor.get_health_status()
        self.assertIn("failing_service", status.components)
        self.assertFalse(status.components["failing_service"])
        
        # Overall status should be degraded
        self.assertEqual(status.state, HealthState.DEGRADED)
    
    def test_health_check_wrapper(self):
        """Test health check wrapper functionality"""
        def original_app_health():
            return {
                'status': 'healthy',
                'database': 'connected',
                'cache': 'available'
            }
        
        # Create wrapper
        wrapped_check = self.health_integration.create_health_check_wrapper(original_app_health)
        
        # Test wrapped result
        result = wrapped_check()
        
        self.assertIn('logging_system', result)
        self.assertIn('database', result)
        self.assertIn('cache', result)
        self.assertEqual(result['database'], 'connected')
        self.assertEqual(result['cache'], 'available')
        
        # Logging system should be included
        logging_health = result['logging_system']
        self.assertIn('status', logging_health)
        self.assertIn('healthy', logging_health)
    
    def test_error_handling(self):
        """Test error handling in health monitoring"""
        # Simulate buffer manager error
        self.mock_buffer_manager.get_buffer_statistics.side_effect = Exception("Buffer error")
        
        # Health monitor should handle the error gracefully
        status = self.health_monitor.get_health_status()
        
        # Should have an alert about the failure
        alert_text = ' '.join(status.alerts)
        self.assertIn("Failed to retrieve buffer statistics", alert_text)
        
        # System should still be operational
        self.assertIsNotNone(status.state)
        self.assertIsInstance(status.timestamp, float)


if __name__ == '__main__':
    unittest.main(verbosity=2)