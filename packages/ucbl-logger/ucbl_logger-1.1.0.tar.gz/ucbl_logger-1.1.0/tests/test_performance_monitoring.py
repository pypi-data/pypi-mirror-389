"""
Comprehensive unit tests for performance monitoring system
"""

import unittest
import time
import logging
from unittest.mock import Mock, patch
from collections import namedtuple

from ucbl_logger.enhanced.performance import (
    EnhancedPerformanceMonitor, PerformanceThresholds, SystemMetrics,
    CPUMetrics, MemoryMetrics, DiskMetrics, NetworkMetrics, PerformanceAlert,
    PerformanceLoggingIntegration, PerformanceAwareLogger
)


class TestPerformanceModels(unittest.TestCase):
    """Test performance monitoring data models"""
    
    def test_cpu_metrics_creation(self):
        """Test CPUMetrics creation and properties"""
        cpu_metrics = CPUMetrics(
            percent=75.5,
            per_cpu_percent=[70.0, 80.0, 75.0, 76.0],
            count_logical=4,
            count_physical=2,
            load_avg_1min=1.5
        )
        
        self.assertEqual(cpu_metrics.percent, 75.5)
        self.assertEqual(len(cpu_metrics.per_cpu_percent), 4)
        self.assertEqual(cpu_metrics.count_logical, 4)
        self.assertEqual(cpu_metrics.load_avg_1min, 1.5)
    
    def test_memory_metrics_creation(self):
        """Test MemoryMetrics creation and properties"""
        memory_metrics = MemoryMetrics(
            total=8 * 1024 * 1024 * 1024,  # 8GB
            available=4 * 1024 * 1024 * 1024,  # 4GB
            percent=50.0,
            swap_total=2 * 1024 * 1024 * 1024,  # 2GB
            swap_percent=25.0
        )
        
        self.assertEqual(memory_metrics.total, 8 * 1024 * 1024 * 1024)
        self.assertEqual(memory_metrics.percent, 50.0)
        self.assertEqual(memory_metrics.swap_percent, 25.0)
    
    def test_system_metrics_backward_compatibility(self):
        """Test SystemMetrics backward compatibility properties"""
        cpu = CPUMetrics(percent=80.0, load_avg_1min=2.0)
        memory = MemoryMetrics(
            percent=70.0,
            used=4 * 1024 * 1024 * 1024,
            available=2 * 1024 * 1024 * 1024
        )
        disk = DiskMetrics(
            read_bytes_per_sec=1024 * 1024,
            write_bytes_per_sec=512 * 1024
        )
        network = NetworkMetrics(bytes_sent=1000, bytes_recv=2000)
        
        metrics = SystemMetrics(cpu=cpu, memory=memory, disk=disk, network=network)
        
        # Test backward compatibility properties
        self.assertEqual(metrics.cpu_percent, 80.0)
        self.assertEqual(metrics.memory_percent, 70.0)
        self.assertAlmostEqual(metrics.memory_used_mb, 4 * 1024, places=0)
        self.assertAlmostEqual(metrics.disk_io_read_mb, 1.0, places=1)
        self.assertEqual(metrics.network_bytes_sent, 1000)
        self.assertEqual(len(metrics.load_average), 3)
    
    def test_system_metrics_to_dict(self):
        """Test SystemMetrics to_dict conversion"""
        metrics = SystemMetrics()
        metrics_dict = metrics.to_dict()
        
        self.assertIn('timestamp', metrics_dict)
        self.assertIn('cpu', metrics_dict)
        self.assertIn('memory', metrics_dict)
        self.assertIn('disk', metrics_dict)
        self.assertIn('network', metrics_dict)
        
        # Check nested structure
        self.assertIn('percent', metrics_dict['cpu'])
        self.assertIn('total_mb', metrics_dict['memory'])
        self.assertIn('read_bytes_per_sec', metrics_dict['disk'])
        self.assertIn('bytes_sent_per_sec', metrics_dict['network'])


class TestPerformanceThresholds(unittest.TestCase):
    """Test performance threshold checking"""
    
    def setUp(self):
        self.thresholds = PerformanceThresholds(
            cpu_warning_percent=80.0,
            cpu_critical_percent=95.0,
            memory_warning_percent=85.0,
            memory_critical_percent=95.0
        )
    
    def test_cpu_threshold_warning(self):
        """Test CPU warning threshold detection"""
        alert = self.thresholds.check_cpu_threshold(85.0)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "warning")
        self.assertEqual(alert.metric, "cpu_percent")
        self.assertEqual(alert.current_value, 85.0)
        self.assertIn("warning", alert.message.lower())
    
    def test_cpu_threshold_critical(self):
        """Test CPU critical threshold detection"""
        alert = self.thresholds.check_cpu_threshold(97.0)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "critical")
        self.assertEqual(alert.metric, "cpu_percent")
        self.assertEqual(alert.current_value, 97.0)
        self.assertIn("critical", alert.message.lower())
    
    def test_cpu_threshold_normal(self):
        """Test CPU normal operation (no alert)"""
        alert = self.thresholds.check_cpu_threshold(75.0)
        self.assertIsNone(alert)
    
    def test_memory_threshold_detection(self):
        """Test memory threshold detection"""
        # Warning
        alert = self.thresholds.check_memory_threshold(90.0)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "warning")
        
        # Critical
        alert = self.thresholds.check_memory_threshold(96.0)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "critical")
        
        # Normal
        alert = self.thresholds.check_memory_threshold(70.0)
        self.assertIsNone(alert)
    
    def test_swap_threshold_detection(self):
        """Test swap usage threshold detection"""
        alert = self.thresholds.check_swap_threshold(85.0)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "critical")
        self.assertEqual(alert.metric, "swap_percent")
    
    def test_load_average_threshold_detection(self):
        """Test load average threshold detection"""
        alert = self.thresholds.check_load_average_threshold(6.0)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "critical")
        self.assertEqual(alert.metric, "load_average")
    
    def test_network_bandwidth_threshold_detection(self):
        """Test network bandwidth threshold detection"""
        alert = self.thresholds.check_network_bandwidth_threshold(600.0)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, "critical")
        self.assertEqual(alert.metric, "network_bandwidth_mbps")


class TestEnhancedPerformanceMonitor(unittest.TestCase):
    """Test enhanced performance monitor functionality"""
    
    def setUp(self):
        self.thresholds = PerformanceThresholds()
        self.monitor = EnhancedPerformanceMonitor(
            thresholds=self.thresholds,
            collection_interval=1,
            history_size=10
        )
    
    def tearDown(self):
        if self.monitor.monitoring_active:
            self.monitor.stop_monitoring()
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        self.assertIsNotNone(self.monitor.thresholds)
        self.assertEqual(self.monitor.collection_interval, 1)
        self.assertEqual(self.monitor.history_size, 10)
        self.assertFalse(self.monitor.monitoring_active)
    
    @patch('ucbl_logger.enhanced.performance.monitor.psutil')
    def test_collect_cpu_metrics_with_psutil(self, mock_psutil):
        """Test CPU metrics collection with mocked psutil"""
        # Mock psutil responses
        mock_psutil.cpu_percent.side_effect = [75.5, [70.0, 80.0]]
        mock_psutil.cpu_count.side_effect = [4, 2]  # logical, physical
        
        # Mock CPU frequency
        MockFreq = namedtuple('MockFreq', ['current', 'min', 'max'])
        mock_psutil.cpu_freq.return_value = MockFreq(2400.0, 800.0, 3200.0)
        
        # Mock load average
        mock_psutil.getloadavg.return_value = (1.5, 1.2, 1.0)
        
        cpu_metrics = self.monitor.collect_cpu_metrics()
        
        self.assertEqual(cpu_metrics.percent, 75.5)
        self.assertEqual(cpu_metrics.per_cpu_percent, [70.0, 80.0])
        self.assertEqual(cpu_metrics.count_logical, 4)
        self.assertEqual(cpu_metrics.count_physical, 2)
        self.assertEqual(cpu_metrics.freq_current, 2400.0)
        self.assertEqual(cpu_metrics.load_avg_1min, 1.5)
    
    def test_collect_cpu_metrics_mock_mode(self):
        """Test CPU metrics collection in mock mode"""
        # Force mock mode
        self.monitor._use_mock_metrics = True
        
        cpu_metrics = self.monitor.collect_cpu_metrics()
        
        self.assertIsInstance(cpu_metrics, CPUMetrics)
        self.assertGreaterEqual(cpu_metrics.percent, 0.0)
        self.assertGreater(cpu_metrics.count_logical, 0)
    
    @patch('ucbl_logger.enhanced.performance.monitor.psutil')
    def test_collect_memory_metrics_with_psutil(self, mock_psutil):
        """Test memory metrics collection with mocked psutil"""
        # Mock virtual memory
        MockVMem = namedtuple('MockVMem', [
            'total', 'available', 'percent', 'used', 'free',
            'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'
        ])
        mock_psutil.virtual_memory.return_value = MockVMem(
            total=8 * 1024**3, available=4 * 1024**3, percent=50.0,
            used=4 * 1024**3, free=4 * 1024**3, active=2 * 1024**3,
            inactive=1 * 1024**3, buffers=512 * 1024**2, cached=1 * 1024**3,
            shared=256 * 1024**2, slab=128 * 1024**2
        )
        
        # Mock swap memory
        MockSwap = namedtuple('MockSwap', ['total', 'used', 'free', 'percent'])
        mock_psutil.swap_memory.return_value = MockSwap(
            total=2 * 1024**3, used=512 * 1024**2, free=1.5 * 1024**3, percent=25.0
        )
        
        memory_metrics = self.monitor.collect_memory_metrics()
        
        self.assertEqual(memory_metrics.total, 8 * 1024**3)
        self.assertEqual(memory_metrics.percent, 50.0)
        self.assertEqual(memory_metrics.swap_percent, 25.0)
    
    @patch('ucbl_logger.enhanced.performance.monitor.psutil')
    def test_collect_disk_metrics_with_psutil(self, mock_psutil):
        """Test disk metrics collection with mocked psutil"""
        # Mock disk I/O counters
        MockDiskIO = namedtuple('MockDiskIO', [
            'read_count', 'write_count', 'read_bytes', 'write_bytes',
            'read_time', 'write_time', 'busy_time'
        ])
        mock_psutil.disk_io_counters.return_value = MockDiskIO(
            read_count=1000, write_count=500, read_bytes=1024**3,
            write_bytes=512 * 1024**2, read_time=5000, write_time=2500,
            busy_time=7500
        )
        
        # Mock disk usage
        MockDiskUsage = namedtuple('MockDiskUsage', ['total', 'used', 'free'])
        mock_psutil.disk_usage.return_value = MockDiskUsage(
            total=100 * 1024**3, used=50 * 1024**3, free=50 * 1024**3
        )
        
        disk_metrics = self.monitor.collect_disk_metrics()
        
        self.assertEqual(disk_metrics.read_count, 1000)
        self.assertEqual(disk_metrics.write_count, 500)
        self.assertEqual(disk_metrics.total_space, 100 * 1024**3)
        self.assertEqual(disk_metrics.usage_percent, 50.0)
    
    @patch('ucbl_logger.enhanced.performance.monitor.psutil')
    def test_collect_network_metrics_with_psutil(self, mock_psutil):
        """Test network metrics collection with mocked psutil"""
        # Mock network I/O counters
        MockNetIO = namedtuple('MockNetIO', [
            'bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv',
            'errin', 'errout', 'dropin', 'dropout'
        ])
        mock_psutil.net_io_counters.return_value = MockNetIO(
            bytes_sent=1024**2, bytes_recv=2 * 1024**2, packets_sent=1000,
            packets_recv=2000, errin=5, errout=3, dropin=2, dropout=1
        )
        
        network_metrics = self.monitor.collect_network_metrics()
        
        self.assertEqual(network_metrics.bytes_sent, 1024**2)
        self.assertEqual(network_metrics.bytes_recv, 2 * 1024**2)
        self.assertEqual(network_metrics.errin, 5)
        self.assertEqual(network_metrics.errout, 3)
    
    def test_collect_system_metrics(self):
        """Test comprehensive system metrics collection"""
        metrics = self.monitor.collect_system_metrics()
        
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertIsInstance(metrics.cpu, CPUMetrics)
        self.assertIsInstance(metrics.memory, MemoryMetrics)
        self.assertIsInstance(metrics.disk, DiskMetrics)
        self.assertIsInstance(metrics.network, NetworkMetrics)
        self.assertGreater(metrics.timestamp, 0)
    
    def test_metrics_history_management(self):
        """Test metrics history storage and retrieval"""
        # Collect some metrics
        for _ in range(5):
            self.monitor.collect_system_metrics()
            time.sleep(0.1)
        
        # Check history
        history = self.monitor.get_metrics_history(duration_seconds=10)
        self.assertGreaterEqual(len(history), 5)
        
        # Check history limit
        for _ in range(20):  # Exceed history_size of 10
            self.monitor.collect_system_metrics()
        
        self.assertLessEqual(len(self.monitor.metrics_history), 10)
    
    def test_performance_alert_generation(self):
        """Test performance alert generation"""
        # Create metrics that should trigger alerts
        cpu_metrics = CPUMetrics(percent=98.0)  # Critical
        memory_metrics = MemoryMetrics(percent=90.0, swap_percent=85.0)  # Warning + Critical
        metrics = SystemMetrics(cpu=cpu_metrics, memory=memory_metrics)
        
        alerts = self.monitor.generate_performance_alerts(metrics)
        
        # Should have at least CPU critical and swap critical alerts
        self.assertGreater(len(alerts), 0)
        
        # Check for specific alert types
        alert_metrics = [alert.metric for alert in alerts]
        self.assertIn('cpu_percent', alert_metrics)
        self.assertIn('swap_percent', alert_metrics)
    
    def test_monitoring_start_stop(self):
        """Test background monitoring start/stop"""
        self.assertFalse(self.monitor.monitoring_active)
        
        # Start monitoring
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.monitoring_active)
        self.assertIsNotNone(self.monitor.monitoring_thread)
        
        # Let it run briefly
        time.sleep(0.5)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring_active)
    
    def test_load_summary(self):
        """Test current load summary generation"""
        summary = self.monitor.get_current_load_summary()
        
        self.assertIn('cpu_percent', summary)
        self.assertIn('memory_percent', summary)
        self.assertIn('disk_usage_percent', summary)
        self.assertIn('load_avg_1min', summary)
        self.assertIn('network_mbps_total', summary)


class TestPerformanceLoggingIntegration(unittest.TestCase):
    """Test performance logging integration"""
    
    def setUp(self):
        self.monitor = EnhancedPerformanceMonitor()
        self.logger = Mock(spec=logging.Logger)
        self.integration = PerformanceLoggingIntegration(
            performance_monitor=self.monitor,
            logger=self.logger,
            periodic_logging_interval=1
        )
    
    def tearDown(self):
        if self.integration.integration_active:
            self.integration.stop_periodic_logging()
    
    def test_integration_initialization(self):
        """Test integration initialization"""
        self.assertEqual(self.integration.performance_monitor, self.monitor)
        self.assertEqual(self.integration.logger, self.logger)
        self.assertEqual(self.integration.periodic_logging_interval, 1)
        self.assertFalse(self.integration.integration_active)
    
    def test_add_performance_context_to_log_entry(self):
        """Test adding performance context to log entries"""
        log_entry = {'message': 'test message', 'level': 'INFO'}
        
        enhanced_entry = self.integration.add_performance_context_to_log_entry(log_entry)
        
        self.assertIn('performance_context', enhanced_entry)
        context = enhanced_entry['performance_context']
        self.assertIn('cpu_percent', context)
        self.assertIn('memory_percent', context)
        self.assertIn('timestamp', context)
    
    def test_performance_aware_sampling(self):
        """Test performance-aware log sampling"""
        # Test with low load (should keep logs)
        self.integration.current_system_load = 50.0
        self.assertTrue(self.integration.should_sample_based_on_performance('INFO'))
        
        # Test with high load (should reduce sampling)
        self.integration.current_system_load = 95.0
        # Error logs should always be kept
        self.assertTrue(self.integration.should_sample_based_on_performance('ERROR'))
        
        # Test sampling rate adjustment
        rate = self.integration.get_performance_aware_sampling_rate()
        self.assertLess(rate, self.integration.base_sampling_rate)
    
    def test_log_performance_metrics(self):
        """Test performance metrics logging"""
        self.integration.log_performance_metrics()
        
        # Verify logger was called
        self.logger.info.assert_called()
        call_args = self.logger.info.call_args[0][0]
        self.assertIn('Performance metrics', call_args)
    
    def test_alert_handling_with_cooldown(self):
        """Test performance alert handling with cooldown logic"""
        alert = PerformanceAlert(
            level="warning",
            metric="cpu_percent",
            current_value=85.0,
            threshold_value=80.0,
            message="CPU usage warning"
        )
        
        # First alert should be logged
        self.integration._handle_performance_alert(alert)
        self.logger.warning.assert_called()
        
        # Reset mock
        self.logger.reset_mock()
        
        # Second alert immediately should be skipped due to cooldown
        self.integration._handle_performance_alert(alert)
        self.logger.warning.assert_not_called()
    
    def test_significant_system_event_logging(self):
        """Test logging significant system events with performance context"""
        event_data = {'component': 'test', 'action': 'restart'}
        
        self.integration.log_significant_system_event(
            "Test system event", event_data
        )
        
        self.logger.info.assert_called()
        call_args = self.logger.info.call_args[0][0]
        self.assertIn('System event with performance context', call_args)
    
    def test_periodic_logging_start_stop(self):
        """Test periodic logging start/stop functionality"""
        self.assertFalse(self.integration.integration_active)
        
        # Start periodic logging
        self.integration.start_periodic_logging()
        self.assertTrue(self.integration.integration_active)
        self.assertIsNotNone(self.integration.periodic_logging_thread)
        
        # Let it run briefly
        time.sleep(0.5)
        
        # Stop periodic logging
        self.integration.stop_periodic_logging()
        self.assertFalse(self.integration.integration_active)
    
    def test_performance_statistics(self):
        """Test performance statistics generation"""
        # Generate some metrics history
        for _ in range(3):
            self.monitor.collect_system_metrics()
            time.sleep(0.1)
        
        stats = self.integration.get_performance_statistics()
        
        self.assertIn('metrics_count', stats)
        self.assertIn('cpu_stats', stats)
        self.assertIn('memory_stats', stats)
        self.assertIn('current_sampling_rate', stats)


class TestPerformanceAwareLogger(unittest.TestCase):
    """Test performance-aware logger wrapper"""
    
    def setUp(self):
        self.base_logger = Mock(spec=logging.Logger)
        self.monitor = EnhancedPerformanceMonitor()
        self.integration = PerformanceLoggingIntegration(
            performance_monitor=self.monitor,
            logger=self.base_logger
        )
        self.perf_logger = PerformanceAwareLogger(
            base_logger=self.base_logger,
            performance_integration=self.integration
        )
    
    def test_logger_initialization(self):
        """Test performance-aware logger initialization"""
        self.assertEqual(self.perf_logger.base_logger, self.base_logger)
        self.assertEqual(self.perf_logger.performance_integration, self.integration)
    
    def test_info_logging_with_performance_context(self):
        """Test info logging with performance context"""
        self.perf_logger.info("Test message")
        
        # Verify base logger was called
        self.base_logger.log.assert_called()
        call_args = self.base_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.INFO)  # Log level
        self.assertIn("Test message", call_args[0][1])  # Message
        self.assertIn("Performance:", call_args[0][1])  # Performance context
    
    def test_error_logging_always_preserved(self):
        """Test that error logs are always preserved regardless of sampling"""
        # Set high system load to trigger sampling
        self.integration.current_system_load = 95.0
        
        self.perf_logger.error("Critical error message")
        
        # Error should still be logged despite high load
        self.base_logger.log.assert_called()
        call_args = self.base_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.ERROR)
    
    def test_all_log_levels(self):
        """Test all log levels work correctly"""
        test_message = "Test message"
        
        # Test each log level
        self.perf_logger.debug(test_message)
        self.perf_logger.info(test_message)
        self.perf_logger.warning(test_message)
        self.perf_logger.error(test_message)
        self.perf_logger.critical(test_message)
        
        # Verify all calls were made
        self.assertEqual(self.base_logger.log.call_count, 5)


if __name__ == '__main__':
    unittest.main()