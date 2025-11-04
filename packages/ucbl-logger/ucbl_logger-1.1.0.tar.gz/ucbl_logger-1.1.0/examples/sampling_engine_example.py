"""
Example demonstrating the intelligent log sampling engine
"""

import time
import random
from ucbl_logger.enhanced.sampling import (
    AdvancedSamplingEngine, SamplingConfig, SamplingStrategy, LogLevel,
    create_sampling_integration, SamplingMonitor
)


def demonstrate_basic_sampling():
    """Demonstrate basic sampling functionality"""
    print("=== Basic Sampling Demonstration ===")
    
    # Create sampling configuration
    config = SamplingConfig(
        enabled=True,
        strategy=SamplingStrategy.ADAPTIVE,
        volume_threshold=50,
        preserve_errors=True,
        debug_mode=False
    )
    
    # Create sampling engine
    engine = AdvancedSamplingEngine(config)
    
    print(f"Initial sampling rate: {engine.current_adaptive_rate}")
    
    # Simulate various log levels
    log_levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
    
    print("\nSampling decisions for different log levels:")
    for level in log_levels:
        decision = engine.should_sample(level, 'demo_logger')
        print(f"{level.value:8}: Sample={decision.should_sample:5} Rate={decision.sampling_rate:.3f} Reason={decision.reason}")
    
    return engine


def demonstrate_volume_based_sampling():
    """Demonstrate volume-based sampling behavior"""
    print("\n=== Volume-Based Sampling Demonstration ===")
    
    config = SamplingConfig(
        strategy=SamplingStrategy.VOLUME_BASED,
        volume_threshold=20,
        high_volume_threshold=50
    )
    
    engine = AdvancedSamplingEngine(config)
    
    print("Simulating increasing log volume...")
    
    # Simulate low volume
    print("\nLow volume (< threshold):")
    for i in range(3):
        decision = engine.should_sample(LogLevel.INFO, 'demo_logger')
        print(f"  Decision {i+1}: Sample={decision.should_sample} Rate={decision.sampling_rate:.3f}")
    
    # Simulate medium volume
    print("\nMedium volume (> threshold, < high threshold):")
    for _ in range(25):  # Exceed normal threshold
        engine._update_volume_tracking()
    
    for i in range(3):
        decision = engine.should_sample(LogLevel.INFO, 'demo_logger')
        print(f"  Decision {i+1}: Sample={decision.should_sample} Rate={decision.sampling_rate:.3f}")
    
    # Simulate high volume
    print("\nHigh volume (> high threshold):")
    for _ in range(30):  # Exceed high threshold
        engine._update_volume_tracking()
    
    for i in range(3):
        decision = engine.should_sample(LogLevel.INFO, 'demo_logger')
        print(f"  Decision {i+1}: Sample={decision.should_sample} Rate={decision.sampling_rate:.3f}")


def demonstrate_adaptive_sampling():
    """Demonstrate adaptive sampling with pattern detection"""
    print("\n=== Adaptive Sampling Demonstration ===")
    
    config = SamplingConfig(
        strategy=SamplingStrategy.ADAPTIVE,
        volume_threshold=30,
        adaptive_enabled=True,
        adaptive_adjustment_factor=0.2
    )
    
    engine = AdvancedSamplingEngine(config)
    
    print("Simulating volume spike pattern...")
    
    # Baseline volume
    print("\nBaseline volume:")
    for _ in range(10):
        engine._update_volume_tracking()
    
    decision = engine.should_sample(LogLevel.INFO, 'demo_logger')
    print(f"Baseline rate: {decision.sampling_rate:.3f}")
    
    # Volume spike
    print("\nVolume spike:")
    for _ in range(100):  # Create spike
        engine._update_volume_tracking()
    
    decision = engine.should_sample(LogLevel.INFO, 'demo_logger')
    print(f"Spike rate: {decision.sampling_rate:.3f}")
    
    # Check dynamic adjustment metadata
    stats = engine.get_sampling_statistics()
    if 'dynamic_adjustment' in stats:
        patterns = stats['dynamic_adjustment'].get('detected_patterns', [])
        print(f"Detected patterns: {len(patterns)}")
        for pattern in patterns:
            print(f"  - {pattern['type']} (confidence: {pattern['confidence']:.2f})")


def demonstrate_debug_mode():
    """Demonstrate debug mode functionality"""
    print("\n=== Debug Mode Demonstration ===")
    
    config = SamplingConfig(
        strategy=SamplingStrategy.ADAPTIVE,
        volume_threshold=10
    )
    
    engine = AdvancedSamplingEngine(config)
    
    # Normal mode
    print("Normal mode:")
    decision = engine.should_sample(LogLevel.DEBUG, 'demo_logger')
    print(f"  DEBUG level: Sample={decision.should_sample} Rate={decision.sampling_rate:.3f}")
    
    # Enable debug mode
    print("\nDebug mode enabled:")
    engine.enable_debug_mode()
    decision = engine.should_sample(LogLevel.DEBUG, 'demo_logger')
    print(f"  DEBUG level: Sample={decision.should_sample} Rate={decision.sampling_rate:.3f}")
    print(f"  Reason: {decision.reason}")
    
    # Disable debug mode
    print("\nDebug mode disabled:")
    engine.disable_debug_mode()
    decision = engine.should_sample(LogLevel.DEBUG, 'demo_logger')
    print(f"  DEBUG level: Sample={decision.should_sample} Rate={decision.sampling_rate:.3f}")


def demonstrate_pipeline_integration():
    """Demonstrate pipeline integration"""
    print("\n=== Pipeline Integration Demonstration ===")
    
    # Create sampling integration
    config = SamplingConfig(
        enabled=True,
        strategy=SamplingStrategy.ADAPTIVE,
        volume_threshold=20
    )
    
    def statistics_callback(stats):
        print(f"Statistics update: {stats['pipeline_statistics']['total_log_entries']} logs processed")
    
    integrator = create_sampling_integration(
        sampling_config=config,
        debug_mode=False,
        statistics_callback=statistics_callback
    )
    
    print("Processing log entries through pipeline...")
    
    # Simulate log entries
    log_entries = [
        {'level': 'DEBUG', 'message': 'Debug message', 'logger_name': 'app.debug'},
        {'level': 'INFO', 'message': 'Info message', 'logger_name': 'app.main'},
        {'level': 'WARNING', 'message': 'Warning message', 'logger_name': 'app.warn'},
        {'level': 'ERROR', 'message': 'Error message', 'logger_name': 'app.error'},
        {'level': 'CRITICAL', 'message': 'Critical message', 'logger_name': 'app.critical'}
    ]
    
    for entry in log_entries:
        should_continue, updated_entry = integrator.process_log_entry(entry, 'pre_format')
        sampling_info = updated_entry.get('sampling', {})
        
        print(f"  {entry['level']:8}: Sample={should_continue:5} "
              f"Rate={sampling_info.get('sampling_rate', 'N/A'):>5} "
              f"Reason={sampling_info.get('sampling_reason', 'N/A')}")
    
    # Get pipeline statistics
    stats = integrator.get_pipeline_statistics()
    pipeline_stats = stats['pipeline_statistics']
    print(f"\nPipeline Statistics:")
    print(f"  Total entries: {pipeline_stats['total_log_entries']}")
    print(f"  Sampling decisions: {pipeline_stats['sampling_decisions_made']}")


def demonstrate_monitoring():
    """Demonstrate sampling monitoring"""
    print("\n=== Monitoring Demonstration ===")
    
    # Create integrator and monitor
    config = SamplingConfig(
        enabled=True,
        volume_threshold=15,
        adaptive_enabled=True
    )
    
    integrator = create_sampling_integration(config)
    monitor = SamplingMonitor(integrator)
    
    # Add alert callback
    def alert_callback(alert):
        print(f"ALERT [{alert.severity.upper()}]: {alert.message}")
    
    monitor.add_alert_callback(alert_callback)
    
    print("Simulating high volume scenario...")
    
    # Simulate high volume to trigger alerts
    for i in range(100):
        log_entry = {
            'level': random.choice(['DEBUG', 'INFO', 'WARNING']),
            'message': f'Message {i}',
            'logger_name': 'load_test'
        }
        integrator.process_log_entry(log_entry, 'pre_format')
        
        # Update sampling rates periodically
        if i % 20 == 0:
            integrator.update_sampling_rates()
    
    # Run monitoring cycle
    report = monitor.run_monitoring_cycle()
    
    if report:
        print(f"\nMonitoring Report Generated:")
        print(f"  Report ID: {report.report_id}")
        print(f"  Alerts: {len(report.alerts)}")
        print(f"  Recommendations: {len(report.recommendations)}")
        
        if report.recommendations:
            print("  Recommendations:")
            for rec in report.recommendations[:3]:  # Show first 3
                print(f"    - {rec}")


def demonstrate_performance_under_load():
    """Demonstrate performance under high load"""
    print("\n=== Performance Under Load Demonstration ===")
    
    config = SamplingConfig(
        strategy=SamplingStrategy.ADAPTIVE,
        volume_threshold=100,
        adaptive_enabled=True
    )
    
    engine = AdvancedSamplingEngine(config)
    
    # Measure performance
    num_decisions = 10000
    start_time = time.time()
    
    print(f"Making {num_decisions} sampling decisions...")
    
    sampled_count = 0
    for i in range(num_decisions):
        level = random.choice(list(LogLevel))
        decision = engine.should_sample(level, f'logger_{i % 100}')
        if decision.should_sample:
            sampled_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Performance Results:")
    print(f"  Total decisions: {num_decisions}")
    print(f"  Time taken: {duration:.3f} seconds")
    print(f"  Decisions per second: {num_decisions / duration:.0f}")
    print(f"  Sampled logs: {sampled_count} ({sampled_count/num_decisions:.1%})")
    
    # Get final statistics
    stats = engine.get_sampling_statistics()
    print(f"  Final sampling efficiency: {stats['statistics']['sampling_efficiency']:.3f}")


def main():
    """Run all demonstrations"""
    print("Intelligent Log Sampling Engine Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_basic_sampling()
        demonstrate_volume_based_sampling()
        demonstrate_adaptive_sampling()
        demonstrate_debug_mode()
        demonstrate_pipeline_integration()
        demonstrate_monitoring()
        demonstrate_performance_under_load()
        
        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()