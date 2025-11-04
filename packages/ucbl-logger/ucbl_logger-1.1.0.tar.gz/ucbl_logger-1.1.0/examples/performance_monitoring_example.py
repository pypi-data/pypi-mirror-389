#!/usr/bin/env python3
"""
Example demonstrating enhanced performance monitoring capabilities
"""

import time
import logging
import threading
from ucbl_logger.enhanced.performance import (
    EnhancedPerformanceMonitor, PerformanceThresholds,
    PerformanceLoggingIntegration, PerformanceAwareLogger
)


def setup_logging():
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('performance_example')


def demonstrate_basic_monitoring():
    """Demonstrate basic performance monitoring"""
    print("\n=== Basic Performance Monitoring ===")
    
    # Create performance monitor with custom thresholds
    thresholds = PerformanceThresholds(
        cpu_warning_percent=70.0,
        cpu_critical_percent=90.0,
        memory_warning_percent=75.0,
        memory_critical_percent=90.0
    )
    
    monitor = EnhancedPerformanceMonitor(
        thresholds=thresholds,
        collection_interval=2,
        history_size=50
    )
    
    # Collect current metrics
    print("Collecting system metrics...")
    metrics = monitor.collect_system_metrics()
    
    print(f"CPU Usage: {metrics.cpu.percent:.1f}%")
    print(f"Memory Usage: {metrics.memory.percent:.1f}%")
    print(f"Load Average (1min): {metrics.cpu.load_avg_1min:.2f}")
    print(f"Disk Usage: {metrics.disk.usage_percent:.1f}%")
    print(f"Network Bandwidth: {(metrics.network.bytes_sent_per_sec + metrics.network.bytes_recv_per_sec) / (1024*1024):.2f} MB/s")
    
    # Check for performance alerts
    alerts = monitor.generate_performance_alerts(metrics)
    if alerts:
        print(f"\nPerformance Alerts ({len(alerts)}):")
        for alert in alerts:
            print(f"  {alert.level.upper()}: {alert.message}")
    else:
        print("\nNo performance alerts detected.")
    
    return monitor


def demonstrate_network_interface_monitoring(monitor):
    """Demonstrate detailed network interface monitoring"""
    print("\n=== Network Interface Monitoring ===")
    
    interface_metrics = monitor.collect_network_interface_metrics()
    
    if interface_metrics:
        print("Network Interface Statistics:")
        for interface, stats in interface_metrics.items():
            print(f"\n  Interface: {interface}")
            print(f"    Bytes sent/sec: {stats['bytes_sent_per_sec']:,.0f}")
            print(f"    Bytes recv/sec: {stats['bytes_recv_per_sec']:,.0f}")
            print(f"    Packets sent/sec: {stats['packets_sent_per_sec']:.1f}")
            print(f"    Packets recv/sec: {stats['packets_recv_per_sec']:.1f}")
            print(f"    Errors in: {stats['errors_in']}")
            print(f"    Errors out: {stats['errors_out']}")
    else:
        print("No active network interfaces detected.")


def demonstrate_performance_logging_integration():
    """Demonstrate performance logging integration"""
    print("\n=== Performance Logging Integration ===")
    
    logger = setup_logging()
    monitor = EnhancedPerformanceMonitor(collection_interval=1)
    
    # Create performance logging integration
    integration = PerformanceLoggingIntegration(
        performance_monitor=monitor,
        logger=logger,
        periodic_logging_interval=3
    )
    
    # Configure performance-aware sampling
    integration.configure_performance_aware_sampling(
        enabled=True,
        base_rate=1.0,
        load_threshold=80.0
    )
    
    # Create performance-aware logger
    perf_logger = PerformanceAwareLogger(logger, integration)
    
    print("Starting performance logging integration...")
    
    # Start periodic logging
    integration.start_periodic_logging()
    
    # Demonstrate logging with performance context
    perf_logger.info("Application started successfully")
    perf_logger.debug("Debug message with performance context")
    
    # Simulate some system events
    integration.log_significant_system_event(
        "Database connection established",
        {"database": "postgresql", "connection_pool_size": 10}
    )
    
    # Let it run for a few seconds
    print("Monitoring performance for 5 seconds...")
    time.sleep(5)
    
    # Get performance statistics
    stats = integration.get_performance_statistics()
    print(f"\nPerformance Statistics:")
    print(f"  Metrics collected: {stats.get('metrics_count', 0)}")
    print(f"  Current sampling rate: {stats.get('current_sampling_rate', 0):.2f}")
    
    if 'cpu_stats' in stats:
        cpu_stats = stats['cpu_stats']
        print(f"  CPU - Avg: {cpu_stats['avg']:.1f}%, Min: {cpu_stats['min']:.1f}%, Max: {cpu_stats['max']:.1f}%")
    
    # Stop periodic logging
    integration.stop_periodic_logging()
    print("Performance logging integration stopped.")
    
    return integration


def demonstrate_background_monitoring():
    """Demonstrate background performance monitoring"""
    print("\n=== Background Monitoring ===")
    
    monitor = EnhancedPerformanceMonitor(collection_interval=1, history_size=20)
    
    print("Starting background monitoring...")
    monitor.start_monitoring()
    
    # Let it collect metrics for a few seconds
    time.sleep(3)
    
    # Get metrics history
    history = monitor.get_metrics_history(duration_seconds=10)
    print(f"Collected {len(history)} metrics in history")
    
    if history:
        latest = history[-1]
        oldest = history[0]
        print(f"Time range: {oldest.timestamp:.1f} to {latest.timestamp:.1f}")
        
        # Show trend
        cpu_values = [m.cpu.percent for m in history]
        memory_values = [m.memory.percent for m in history]
        
        print(f"CPU trend: {min(cpu_values):.1f}% - {max(cpu_values):.1f}%")
        print(f"Memory trend: {min(memory_values):.1f}% - {max(memory_values):.1f}%")
    
    # Get current load summary
    summary = monitor.get_current_load_summary()
    print(f"\nCurrent Load Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value:.2f}")
    
    monitor.stop_monitoring()
    print("Background monitoring stopped.")


def simulate_high_load_scenario():
    """Simulate a high load scenario to test alerting"""
    print("\n=== High Load Simulation ===")
    
    # Create monitor with low thresholds for demonstration
    thresholds = PerformanceThresholds(
        cpu_warning_percent=1.0,  # Very low to trigger alerts
        cpu_critical_percent=5.0,
        memory_warning_percent=1.0,
        memory_critical_percent=5.0
    )
    
    monitor = EnhancedPerformanceMonitor(thresholds=thresholds)
    logger = setup_logging()
    
    integration = PerformanceLoggingIntegration(
        performance_monitor=monitor,
        logger=logger
    )
    
    # Collect metrics (should trigger alerts with low thresholds)
    metrics = monitor.collect_system_metrics()
    alerts = monitor.generate_performance_alerts(metrics)
    
    print(f"Generated {len(alerts)} alerts with low thresholds:")
    for alert in alerts:
        print(f"  {alert.level.upper()}: {alert.message}")
        integration._handle_performance_alert(alert)
    
    # Test alert cooldown
    print("\nTesting alert cooldown (should skip duplicate alerts)...")
    for alert in alerts[:2]:  # Test first 2 alerts
        integration._handle_performance_alert(alert)  # Should be skipped


def main():
    """Main demonstration function"""
    print("Enhanced Performance Monitoring Demonstration")
    print("=" * 50)
    
    try:
        # Basic monitoring
        monitor = demonstrate_basic_monitoring()
        
        # Network interface monitoring
        demonstrate_network_interface_monitoring(monitor)
        
        # Performance logging integration
        demonstrate_performance_logging_integration()
        
        # Background monitoring
        demonstrate_background_monitoring()
        
        # High load simulation
        simulate_high_load_scenario()
        
        print("\n" + "=" * 50)
        print("Performance monitoring demonstration completed successfully!")
        
    except KeyboardInterrupt:
        print("\nDemonstration interrupted by user.")
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()