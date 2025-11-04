"""
Unit tests for health monitoring components
"""

import unittest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from io import StringIO

# Import health monitoring components
from ucbl_logger.enhanced.health import (
    HealthMonitor, 
    BaseHealthMonitor,
    HealthStatus, 
    HealthState,
    HealthEndpoint
)

try:
    from ucbl_logger.enhanced.health.metrics import (
        HealthMetricsCollector,
        HealthAlerting,
        IntegratedHealthMetrics,
        Alert,
        AlertSeverity,
        MetricPoint
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

from ucbl_logger.enhanced.health.integration import (
    HealthIntegration,
    KubernetesHealthIntegration
)


class TestHealthStatus(unittest.TestCase):
    """Test HealthStatus model"""
    
    def test_health_status_creation(self):
        """Test basic health status creation"""
        status = HealthStatus(
            state=HealthState.HEALTHY,
            timestamp=time.time(),
            uptime_seconds=100.0
        )
        
        self.assertEqual(status.state, HealthState.HEALTHY)
        self.assertTrue(status.is_healthy())
        self.assertEqual(len(status.components), 0)
        self.assertEqual(len(status.alerts), 0)
    
    def test_add_component_status(self):
        """Test adding component status"""
        status = HealthStatus(state=HealthState.HEALTHY)
        
        status.add_component_status("buffer", True)
        self.assertTrue(status.components["buffer"])
        self.assertEqual(status.state, HealthState.HEALTHY)
        
        status.add_component_status("delivery", False)
        self.assertFalse(status.components["delivery"])
        self.assertEqual(status.state, HealthState.DEGRADED)
    
    def test_add_alert(self):
        """Test adding alerts"""
        status = HealthStatus(state=HealthState.HEALTHY)
        
        status.add_alert("Test alert")
        self.assertIn("Test alert", status.alerts)
        self.assertEqual(status.state, HealthState.DEGRADED)


class TestBaseHealthMonitor(unittest.TestCase):
    """Test BaseHealthMonitor functionality"""
    
    def setUp(self):
        self.monitor = BaseHealthMonitor()
    
    def test_initial_state(self):
        """Test initial health monitor state"""
        status = self.monitor.get_health_status()
        self.assertEqual(status.state, HealthState.UNKNOWN)
        self.assertEqual(len(status.components), 0)
    
    def test_register_health_check(self):
        """Test registering health checks"""
        def dummy_check():
            return True
        
        self.monitor.register_health_check("test_check", dummy_check)
        self.assertIn("test_check", self.monitor.health_checks)
        
        status = self.monitor.get_health_status()
        self.assertEqual(status.state, HealthState.HEALTHY)
        self.assertTrue(status.components["test_check"])
    
    def test_failing_health_check(self):
        """Test health check that fails"""
        def failing_check():
            return False
        
        self.monitor.register_health_check("failing_check", failing_check)
        
        status = self.monitor.get_health_status()
        self.assertEqual(status.state, HealthState.UNHEALTHY)
        self.assertFalse(status.components["failing_check"])
    
    def test_mixed_health_checks(self):
        """Test mix of passing and failing health checks"""
        def passing_check():
            return True
        
        def failing_check():
            return False
        
        self.monitor.register_health_check("passing", passing_check)
        self.monitor.register_health_check("failing", failing_check)
        
        status = self.monitor.get_health_status()
        self.assertEqual(status.state, HealthState.DEGRADED)
        self.assertTrue(status.components["passing"])
        self.assertFalse(status.components["failing"])
    
    def test_exception_in_health_check(self):
        """Test health check that raises exception"""
        def exception_check():
            raise Exception("Test exception")
        
        self.monitor.register_health_check("exception_check", exception_check)
        
        status = self.monitor.get_health_status()
        self.assertEqual(status.state, HealthState.UNHEALTHY)
        self.assertFalse(status.components["exception_check"])
    
    def test_check_component_health(self):
        """Test checking individual component health"""
        def test_check():
            return True
        
        self.monitor.register_health_check("test_component", test_check)
        
        # Check registered component
        self.assertTrue(self.monitor.check_component_health("test_component"))
        
        # Check non-existent component
        self.assertTrue(self.monitor.check_component_health("non_existent"))
    
    def test_get_health_metrics(self):
        """Test getting health metrics"""
        def test_check():
            return True
        
        self.monitor.register_health_check("test", test_check)
        self.monitor.get_health_status()  # Populate component status
        
        metrics = self.monitor.get_health_metrics()
        
        self.assertIn("uptime_seconds", metrics)
        self.assertIn("component_count", metrics)
        self.assertIn("healthy_components", metrics)
        self.assertIn("registered_checks", metrics)
        
        self.assertEqual(metrics["component_count"], 1)
        self.assertEqual(metrics["healthy_components"], 1)
        self.assertIn("test", metrics["registered_checks"])
    
    def test_is_degraded(self):
        """Test degraded state detection"""
        # Initially unknown, not degraded
        self.assertFalse(self.monitor.is_degraded())
        
        # Add healthy check
        self.monitor.register_health_check("healthy", lambda: True)
        self.assertFalse(self.monitor.is_degraded())
        
        # Add failing check
        self.monitor.register_health_check("failing", lambda: False)
        self.assertTrue(self.monitor.is_degraded())
    
    def test_thread_safety(self):
        """Test thread safety of health monitor"""
        results = []
        
        def add_checks():
            for i in range(10):
                self.monitor.register_health_check(f"check_{i}", lambda: True)
                results.append(self.monitor.get_health_status())
        
        threads = [threading.Thread(target=add_checks) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have results from all threads
        self.assertGreater(len(results), 0)
        
        # Final status should be healthy
        final_status = self.monitor.get_health_status()
        self.assertEqual(final_status.state, HealthState.HEALTHY)


class TestHealthMonitor(unittest.TestCase):
    """Test comprehensive HealthMonitor functionality"""
    
    def setUp(self):
        self.mock_buffer_manager = Mock()
        self.mock_delivery_manager = Mock()
        
        # Setup mock buffer manager
        self.mock_buffer_manager.get_buffer_statistics.return_value = {
            'usage_percentage': 0.5,
            'current_size': 500,
            'max_size': 1000
        }
        self.mock_buffer_manager.is_buffer_healthy.return_value = True
        
        # Setup mock delivery manager
        self.mock_delivery_manager.get_delivery_statistics.return_value = {
            'failure_rate': 0.05,
            'total_deliveries': 1000,
            'failed_deliveries': 50
        }
        
        self.monitor = HealthMonitor(
            buffer_manager=self.mock_buffer_manager,
            delivery_manager=self.mock_delivery_manager,
            enable_metrics=False  # Disable metrics for basic tests
        )
    
    def test_buffer_health_check(self):
        """Test buffer health checking"""
        # Test healthy buffer
        self.assertTrue(self.monitor._check_buffer_health())
        
        # Test unhealthy buffer (high usage)
        self.mock_buffer_manager.get_buffer_statistics.return_value = {
            'usage_percentage': 0.96
        }
        self.assertFalse(self.monitor._check_buffer_health())
        
        # Test buffer manager exception
        self.mock_buffer_manager.get_buffer_statistics.side_effect = Exception("Test error")
        self.assertFalse(self.monitor._check_buffer_health())
    
    def test_delivery_health_check(self):
        """Test delivery health checking"""
        # Test healthy delivery
        self.assertTrue(self.monitor._check_delivery_health())
        
        # Test unhealthy delivery (high failure rate)
        self.mock_delivery_manager.get_delivery_statistics.return_value = {
            'failure_rate': 0.15
        }
        self.assertFalse(self.monitor._check_delivery_health())
        
        # Test delivery manager without statistics method
        delattr(self.mock_delivery_manager, 'get_delivery_statistics')
        self.assertTrue(self.monitor._check_delivery_health())  # Falls back to buffer health
    
    def test_system_resources_check(self):
        """Test system resources health check"""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Test healthy system
            mock_memory.return_value.percent = 80
            mock_disk.return_value.percent = 80
            self.assertTrue(self.monitor._check_system_resources())
            
            # Test high memory usage
            mock_memory.return_value.percent = 96
            mock_disk.return_value.percent = 80
            self.assertFalse(self.monitor._check_system_resources())
            
            # Test high disk usage
            mock_memory.return_value.percent = 80
            mock_disk.return_value.percent = 96
            self.assertFalse(self.monitor._check_system_resources())
    
    def test_system_resources_check_no_psutil(self):
        """Test system resources check when psutil is not available"""
        # Mock the import to raise ImportError
        with patch.dict('sys.modules', {'psutil': None}):
            # Should return True when psutil is not available
            self.assertTrue(self.monitor._check_system_resources())
    
    def test_comprehensive_health_status(self):
        """Test comprehensive health status with all components"""
        status = self.monitor.get_health_status()
        
        # Should have default health checks registered
        self.assertIn("buffer_status", status.components)
        self.assertIn("delivery_health", status.components)
        self.assertIn("system_resources", status.components)
        
        # Should include buffer metrics
        self.assertIn("buffer", status.metrics)
    
    def test_kubernetes_health_endpoints(self):
        """Test Kubernetes-specific health endpoints"""
        # Test healthy system
        k8s_health = self.monitor.get_kubernetes_health_endpoint()
        
        self.assertIn("status", k8s_health)
        self.assertIn("timestamp", k8s_health)
        self.assertIn("uptime", k8s_health)
        self.assertIn("components", k8s_health)
        
        # Test readiness and liveness
        self.assertTrue(self.monitor.get_readiness_status())
        self.assertTrue(self.monitor.get_liveness_status())
    
    def test_buffer_threshold_configuration(self):
        """Test buffer threshold configuration"""
        # Test valid thresholds
        self.monitor.set_buffer_thresholds(0.7, 0.9)
        self.assertEqual(self.monitor.buffer_threshold_warning, 0.7)
        self.assertEqual(self.monitor.buffer_threshold_critical, 0.9)
        
        # Test invalid thresholds (should not change)
        original_warning = self.monitor.buffer_threshold_warning
        original_critical = self.monitor.buffer_threshold_critical
        
        self.monitor.set_buffer_thresholds(0.9, 0.7)  # warning > critical
        self.assertEqual(self.monitor.buffer_threshold_warning, original_warning)
        self.assertEqual(self.monitor.buffer_threshold_critical, original_critical)
    
    def test_delivery_threshold_configuration(self):
        """Test delivery failure threshold configuration"""
        # Test valid threshold
        self.monitor.set_delivery_failure_threshold(0.05)
        self.assertEqual(self.monitor.delivery_failure_threshold, 0.05)
        
        # Test invalid threshold (should not change)
        original_threshold = self.monitor.delivery_failure_threshold
        
        self.monitor.set_delivery_failure_threshold(1.5)  # > 1.0
        self.assertEqual(self.monitor.delivery_failure_threshold, original_threshold)
        
        self.monitor.set_delivery_failure_threshold(-0.1)  # < 0.0
        self.assertEqual(self.monitor.delivery_failure_threshold, original_threshold)


class TestHealthEndpoint(unittest.TestCase):
    """Test HealthEndpoint functionality"""
    
    def setUp(self):
        self.mock_monitor = Mock(spec=HealthMonitor)
        self.mock_monitor.get_health_status.return_value = HealthStatus(
            state=HealthState.HEALTHY,
            timestamp=time.time(),
            uptime_seconds=100.0,
            components={"test": True},
            metrics={"uptime": 100.0}
        )
        self.mock_monitor.get_liveness_status.return_value = True
        self.mock_monitor.get_readiness_status.return_value = True
        
        self.endpoint = HealthEndpoint(self.mock_monitor)
    
    def test_health_check_handler(self):
        """Test main health check handler"""
        response = self.endpoint.health_check_handler()
        
        self.assertIn("status", response)
        self.assertIn("timestamp", response)
        self.assertIn("uptime_seconds", response)
        self.assertIn("components", response)
        self.assertIn("metrics", response)
        
        self.assertEqual(response["status"], "healthy")
        self.assertEqual(response["components"], {"test": True})
    
    def test_liveness_probe_handler(self):
        """Test liveness probe handler"""
        response = self.endpoint.liveness_probe_handler()
        
        self.assertIn("status", response)
        self.assertIn("timestamp", response)
        self.assertEqual(response["status"], "alive")
        
        # Test dead status
        self.mock_monitor.get_liveness_status.return_value = False
        response = self.endpoint.liveness_probe_handler()
        self.assertEqual(response["status"], "dead")
    
    def test_readiness_probe_handler(self):
        """Test readiness probe handler"""
        response = self.endpoint.readiness_probe_handler()
        
        self.assertIn("status", response)
        self.assertIn("timestamp", response)
        self.assertIn("state", response)
        self.assertEqual(response["status"], "ready")
        
        # Test not ready status
        self.mock_monitor.get_readiness_status.return_value = False
        response = self.endpoint.readiness_probe_handler()
        self.assertEqual(response["status"], "not_ready")
        self.assertIn("components", response)
    
    def test_metrics_handler(self):
        """Test metrics handler"""
        self.mock_monitor.get_health_metrics.return_value = {
            "uptime_seconds": 100.0,
            "component_count": 1
        }
        
        response = self.endpoint.metrics_handler()
        
        self.assertIn("health", response)
        self.assertIn("components", response)
        self.assertIn("metrics", response)
        self.assertIn("alerts", response)
    
    def test_get_http_status_code(self):
        """Test HTTP status code determination"""
        # Test healthy status
        health_data = {"status": "healthy"}
        self.assertEqual(self.endpoint.get_http_status_code(health_data), 200)
        
        # Test degraded status
        health_data = {"status": "degraded"}
        self.assertEqual(self.endpoint.get_http_status_code(health_data), 200)
        
        # Test unhealthy status
        health_data = {"status": "unhealthy"}
        self.assertEqual(self.endpoint.get_http_status_code(health_data), 503)
        
        # Test unknown status
        health_data = {"status": "unknown"}
        self.assertEqual(self.endpoint.get_http_status_code(health_data), 503)
    
    def test_register_custom_check(self):
        """Test registering custom health checks"""
        def custom_check():
            return True
        
        self.endpoint.register_custom_check("custom", custom_check)
        
        self.assertIn("custom", self.endpoint.custom_checks)
        self.mock_monitor.register_health_check.assert_called_with("custom", custom_check)


@unittest.skipUnless(METRICS_AVAILABLE, "Metrics system not available")
class TestHealthMetrics(unittest.TestCase):
    """Test health metrics functionality"""
    
    def setUp(self):
        self.metrics_collector = HealthMetricsCollector(max_history=100)
        self.alerting = HealthAlerting(max_alerts=50)
    
    def test_metrics_collection(self):
        """Test basic metrics collection"""
        metrics = self.metrics_collector.collect_metrics()
        
        self.assertIn("uptime_seconds", metrics)
        self.assertIn("thread_count", metrics)
        self.assertIsInstance(metrics["uptime_seconds"], float)
        self.assertIsInstance(metrics["thread_count"], float)
    
    def test_custom_metric_registration(self):
        """Test registering custom metrics"""
        def custom_metric():
            return 42.0
        
        self.metrics_collector.register_metric_callback("custom", custom_metric)
        metrics = self.metrics_collector.collect_metrics()
        
        self.assertIn("custom", metrics)
        self.assertEqual(metrics["custom"], 42.0)
    
    def test_metric_history(self):
        """Test metric history tracking"""
        def test_metric():
            return 10.0
        
        self.metrics_collector.register_metric_callback("test", test_metric)
        
        # Collect metrics multiple times
        for _ in range(5):
            self.metrics_collector.collect_metrics()
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        history = self.metrics_collector.get_metric_history("test", duration_seconds=10)
        self.assertEqual(len(history), 5)
        
        for point in history:
            self.assertEqual(point.name, "test")
            self.assertEqual(point.value, 10.0)
    
    def test_metric_statistics(self):
        """Test metric statistics calculation"""
        values = [10.0, 20.0, 30.0]
        
        def varying_metric():
            return values.pop(0) if values else 30.0
        
        self.metrics_collector.register_metric_callback("varying", varying_metric)
        
        # Collect metrics
        for _ in range(3):
            self.metrics_collector.collect_metrics()
        
        stats = self.metrics_collector.get_metric_statistics("varying", duration_seconds=10)
        
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 30.0)
        self.assertEqual(stats["avg"], 20.0)
        self.assertEqual(stats["current"], 30.0)
    
    def test_prometheus_export(self):
        """Test Prometheus metrics export"""
        def test_metric():
            return 42.0
        
        self.metrics_collector.register_metric_callback("test_metric", test_metric)
        self.metrics_collector.collect_metrics()
        
        prometheus_output = self.metrics_collector.export_prometheus_metrics()
        
        self.assertIn("ucbl_logger_test_metric", prometheus_output)
        self.assertIn("42.0", prometheus_output)
        self.assertIn("# TYPE", prometheus_output)
    
    def test_alert_rules(self):
        """Test alert rule functionality"""
        # Add alert rule
        self.alerting.add_alert_rule(
            name="high_value",
            condition=lambda m: m.get("test_metric", 0) > 50,
            severity=AlertSeverity.WARNING,
            message="High value detected: {test_metric}",
            component="test"
        )
        
        # Test condition that should not trigger
        metrics = {"test_metric": 30}
        alerts = self.alerting.check_alert_rules(metrics)
        self.assertEqual(len(alerts), 0)
        
        # Test condition that should trigger
        metrics = {"test_metric": 60}
        alerts = self.alerting.check_alert_rules(metrics)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
        self.assertEqual(alert.component, "test")
        self.assertIn("High value detected", alert.message)
    
    def test_alert_cooldown(self):
        """Test alert cooldown functionality"""
        self.alerting.add_alert_rule(
            name="test_cooldown",
            condition=lambda m: True,  # Always triggers
            severity=AlertSeverity.INFO,
            message="Test alert",
            component="test"
        )
        
        # First check should trigger alert
        alerts1 = self.alerting.check_alert_rules({})
        self.assertEqual(len(alerts1), 1)
        
        # Immediate second check should not trigger (cooldown)
        alerts2 = self.alerting.check_alert_rules({})
        self.assertEqual(len(alerts2), 0)
    
    def test_alert_callbacks(self):
        """Test alert callback functionality"""
        callback_alerts = []
        
        def alert_callback(alert):
            callback_alerts.append(alert)
        
        self.alerting.register_alert_callback(alert_callback)
        
        self.alerting.add_alert_rule(
            name="callback_test",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message="Callback test",
            component="test"
        )
        
        self.alerting.check_alert_rules({})
        
        self.assertEqual(len(callback_alerts), 1)
        self.assertEqual(callback_alerts[0].message, "Callback test")
    
    def test_integrated_metrics_system(self):
        """Test integrated metrics system"""
        integrated = IntegratedHealthMetrics()
        
        result = integrated.collect_and_check()
        
        self.assertIn("metrics", result)
        self.assertIn("new_alerts", result)
        self.assertIn("alert_summary", result)
        
        dashboard_data = integrated.get_dashboard_data()
        
        self.assertIn("current_metrics", dashboard_data)
        self.assertIn("metric_statistics", dashboard_data)
        self.assertIn("active_alerts", dashboard_data)
        self.assertIn("alert_summary", dashboard_data)


class TestHealthIntegration(unittest.TestCase):
    """Test health integration functionality"""
    
    def setUp(self):
        self.mock_monitor = Mock(spec=HealthMonitor)
        self.mock_monitor.get_health_status.return_value = HealthStatus(
            state=HealthState.HEALTHY,
            timestamp=time.time(),
            uptime_seconds=100.0
        )
        self.mock_monitor.get_liveness_status.return_value = True
        self.mock_monitor.get_readiness_status.return_value = True
        
        self.integration = HealthIntegration(self.mock_monitor)
        self.k8s_integration = KubernetesHealthIntegration(self.mock_monitor)
    
    def test_health_summary(self):
        """Test health summary generation"""
        summary = self.integration.get_health_summary()
        
        self.assertIn("logging_system", summary)
        logging_health = summary["logging_system"]
        
        self.assertIn("status", logging_health)
        self.assertIn("healthy", logging_health)
        self.assertIn("uptime_seconds", logging_health)
        self.assertEqual(logging_health["status"], "healthy")
        self.assertTrue(logging_health["healthy"])
    
    def test_merge_with_app_health(self):
        """Test merging with application health"""
        app_health = {
            "status": "healthy",
            "database": "connected",
            "cache": "available"
        }
        
        merged = self.integration.merge_with_app_health(app_health)
        
        self.assertIn("logging_system", merged)
        self.assertIn("database", merged)
        self.assertIn("cache", merged)
        self.assertEqual(merged["status"], "healthy")
    
    def test_merge_with_unhealthy_logging(self):
        """Test merging when logging system is unhealthy"""
        self.mock_monitor.get_health_status.return_value = HealthStatus(
            state=HealthState.UNHEALTHY
        )
        
        app_health = {"status": "healthy"}
        merged = self.integration.merge_with_app_health(app_health)
        
        self.assertEqual(merged["status"], "degraded")
        self.assertIn("issues", merged)
    
    def test_health_check_wrapper(self):
        """Test health check wrapper functionality"""
        def original_check():
            return {"status": "healthy", "service": "running"}
        
        wrapped_check = self.integration.create_health_check_wrapper(original_check)
        result = wrapped_check()
        
        self.assertIn("logging_system", result)
        self.assertIn("service", result)
        self.assertEqual(result["service"], "running")
    
    def test_kubernetes_probes(self):
        """Test Kubernetes probe creation"""
        # Test liveness probe
        liveness_probe = self.k8s_integration.create_liveness_probe()
        result, status_code = liveness_probe()
        
        self.assertEqual(result["status"], "alive")
        self.assertEqual(status_code, 200)
        
        # Test readiness probe
        readiness_probe = self.k8s_integration.create_readiness_probe()
        result, status_code = readiness_probe()
        
        self.assertEqual(result["status"], "ready")
        self.assertEqual(status_code, 200)
        
        # Test startup probe
        startup_probe = self.k8s_integration.create_startup_probe(startup_timeout_seconds=1)
        result, status_code = startup_probe()
        
        self.assertEqual(result["status"], "started")
        self.assertEqual(status_code, 200)
    
    def test_kubernetes_probes_unhealthy(self):
        """Test Kubernetes probes when system is unhealthy"""
        self.mock_monitor.get_liveness_status.return_value = False
        self.mock_monitor.get_readiness_status.return_value = False
        
        # Test liveness probe
        liveness_probe = self.k8s_integration.create_liveness_probe()
        result, status_code = liveness_probe()
        
        self.assertEqual(result["status"], "dead")
        self.assertEqual(status_code, 503)
        
        # Test readiness probe
        readiness_probe = self.k8s_integration.create_readiness_probe()
        result, status_code = readiness_probe()
        
        self.assertEqual(result["status"], "not_ready")
        self.assertEqual(status_code, 503)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestHealthStatus))
    suite.addTest(unittest.makeSuite(TestBaseHealthMonitor))
    suite.addTest(unittest.makeSuite(TestHealthMonitor))
    suite.addTest(unittest.makeSuite(TestHealthEndpoint))
    
    if METRICS_AVAILABLE:
        suite.addTest(unittest.makeSuite(TestHealthMetrics))
    
    suite.addTest(unittest.makeSuite(TestHealthIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)