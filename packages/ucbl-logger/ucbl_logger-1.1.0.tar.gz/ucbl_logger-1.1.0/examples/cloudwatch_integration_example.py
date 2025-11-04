#!/usr/bin/env python3
"""
CloudWatch Integration Example

This example demonstrates how to use the enhanced CloudWatch integration
with intelligent batching, rate limiting, and cost optimization.
"""

import time
import os
from ucbl_logger.enhanced.cloudwatch import (
    CloudWatchConfig, EnhancedCloudWatchHandler, LogEntry,
    CloudWatchAutoConfigurator, MultiDestinationManager,
    CloudWatchDestination, DeliveryMode
)


def basic_cloudwatch_example():
    """Basic CloudWatch integration example."""
    print("=== Basic CloudWatch Integration Example ===")
    
    # Configure CloudWatch
    config = CloudWatchConfig(
        region="us-east-1",
        log_group_name="/aws/eks/my-service/logs",
        log_stream_name="my-service-stream",
        batch_size=10,
        batch_timeout=5.0,
        enable_deduplication=True,
        auto_create_group=True,
        auto_create_stream=True
    )
    
    try:
        # Create handler (will fail without AWS credentials, but shows the API)
        handler = EnhancedCloudWatchHandler(config)
        
        # Send some log entries
        for i in range(5):
            entry = LogEntry(
                timestamp=int(time.time() * 1000),
                message=f"Test log message {i}",
                log_level="INFO",
                metadata={
                    "service": "my-service",
                    "version": "1.0.0",
                    "request_id": f"req-{i}"
                }
            )
            
            success = handler.send_log(entry)
            print(f"Sent log entry {i}: {success}")
        
        # Get statistics
        stats = handler.get_stats()
        print(f"Handler stats: {stats}")
        
        # Get detailed stats
        detailed_stats = handler.get_detailed_stats()
        print(f"Detailed stats: {detailed_stats}")
        
        # Flush and shutdown
        handler.flush()
        handler.shutdown()
        
    except ImportError as e:
        print(f"CloudWatch integration requires boto3: {e}")
    except Exception as e:
        print(f"CloudWatch example failed (expected without AWS credentials): {e}")


def auto_configuration_example():
    """Auto-configuration example."""
    print("\n=== Auto-Configuration Example ===")
    
    try:
        # Create auto-configurator
        configurator = CloudWatchAutoConfigurator(region="us-west-2")
        
        # Auto-configure for a service
        config = configurator.auto_configure(
            service_name="my-graphrag-service",
            environment="development",
            additional_tags={
                "team": "ai-platform",
                "cost-center": "engineering"
            }
        )
        
        print(f"Auto-configured log group: {config.log_group_name}")
        print(f"Auto-configured log stream: {config.log_stream_name}")
        print(f"Default tags: {config.default_tags}")
        
        # Create multi-destination config
        destinations = configurator.create_multi_destination_config(
            service_name="my-service",
            environments=["development", "staging"],
            regions=["us-east-1", "us-west-2"]
        )
        
        print(f"Created {len(destinations)} destinations:")
        for dest in destinations:
            print(f"  - {dest.name} (priority: {dest.priority})")
            
    except ImportError as e:
        print(f"Auto-configuration requires boto3: {e}")
    except Exception as e:
        print(f"Auto-configuration example failed: {e}")


def multi_destination_example():
    """Multi-destination delivery example."""
    print("\n=== Multi-Destination Example ===")
    
    try:
        # Create destinations
        primary_dest = CloudWatchDestination(
            name="primary",
            region="us-east-1",
            log_group="/aws/eks/primary/logs",
            log_stream="primary-stream",
            config=CloudWatchConfig(region="us-east-1"),
            priority=1,
            enabled=True
        )
        
        backup_dest = CloudWatchDestination(
            name="backup",
            region="us-west-2", 
            log_group="/aws/eks/backup/logs",
            log_stream="backup-stream",
            config=CloudWatchConfig(region="us-west-2"),
            priority=2,
            enabled=True
        )
        
        # Create multi-destination manager
        manager = MultiDestinationManager(
            destinations=[primary_dest, backup_dest],
            delivery_mode=DeliveryMode.PARALLEL
        )
        
        # Send log entry to all destinations
        entry = LogEntry(
            timestamp=int(time.time() * 1000),
            message="Multi-destination test message",
            log_level="INFO"
        )
        
        results = manager.send_log_to_all(entry)
        print(f"Delivery results: {results}")
        
        # Get health status
        health = manager.get_health_status()
        print(f"Destination health: {health}")
        
        # Get summary stats
        summary = manager.get_summary_stats()
        print(f"Summary stats: {summary}")
        
        # Shutdown
        manager.shutdown()
        
    except ImportError as e:
        print(f"Multi-destination requires boto3: {e}")
    except Exception as e:
        print(f"Multi-destination example failed: {e}")


def cost_optimization_example():
    """Cost optimization example."""
    print("\n=== Cost Optimization Example ===")
    
    from ucbl_logger.enhanced.cloudwatch import CostOptimizer, LogBatch
    
    # Create cost optimizer
    optimizer = CostOptimizer()
    
    # Create a batch with various log entries
    batch = LogBatch()
    
    # Add entries with different characteristics
    entries = [
        LogEntry(
            timestamp=int(time.time() * 1000),
            message="Normal log message",
            log_level="INFO",
            metadata={"service": "test"}
        ),
        LogEntry(
            timestamp=int(time.time() * 1000),
            message="Very long log message with lots of details " + "x" * 1000,
            log_level="DEBUG",
            metadata={
                "service": "test",
                "large_field": "y" * 2000,
                "empty_field": "",
                "null_field": None
            }
        ),
        LogEntry(
            timestamp=int(time.time() * 1000),
            message="Error message",
            log_level="ERROR",
            metadata={"service": "test", "error_code": "E001"}
        )
    ]
    
    for entry in entries:
        batch.add_entry(entry)
    
    print(f"Original batch size: {batch.get_size_bytes()} bytes")
    
    # Optimize the batch
    optimized_batch = optimizer.optimize_batch(batch)
    print(f"Optimized batch size: {optimized_batch.get_size_bytes()} bytes")
    
    # Get cost stats
    cost_stats = optimizer.get_cost_stats()
    print(f"Cost stats: {cost_stats}")
    
    # Estimate monthly costs
    monthly_estimate = optimizer.estimate_monthly_cost(daily_log_volume_gb=1.0)
    print(f"Monthly cost estimate for 1GB/day: {monthly_estimate}")


def compression_and_deduplication_example():
    """Compression and deduplication example."""
    print("\n=== Compression and Deduplication Example ===")
    
    from ucbl_logger.enhanced.cloudwatch import (
        LogCompressor, LogDeduplicator, CompressionConfig, CompressionType, LogBatch
    )
    
    # Create compressor
    compression_config = CompressionConfig(
        compression_type=CompressionType.GZIP,
        compression_level=6,
        threshold_bytes=100
    )
    compressor = LogCompressor(compression_config)
    
    # Create deduplicator
    deduplicator = LogDeduplicator(window_seconds=300)
    
    # Create test batch
    batch = LogBatch()
    
    # Add multiple entries (some duplicates)
    messages = [
        "First unique message",
        "Second unique message", 
        "First unique message",  # Duplicate
        "Third unique message",
        "Second unique message"  # Duplicate
    ]
    
    for i, message in enumerate(messages):
        entry = LogEntry(
            timestamp=int(time.time() * 1000) + i,
            message=message,
            log_level="INFO"
        )
        
        # Check for duplicates
        is_duplicate = deduplicator.is_duplicate(entry)
        print(f"Entry {i}: '{message}' - Duplicate: {is_duplicate}")
        
        if not is_duplicate:
            batch.add_entry(entry)
    
    print(f"Batch after deduplication: {batch.size()} entries")
    
    # Compress the batch
    should_compress = compressor.should_compress(batch)
    print(f"Should compress batch: {should_compress}")
    
    if should_compress:
        compressed_batch = compressor.compress_batch(batch)
        print(f"Compression applied: {compressed_batch.compressed}")
        if compressed_batch.compressed:
            print(f"Original size: {compressed_batch.original_size} bytes")
            print(f"Compressed size: {compressed_batch.compressed_size} bytes")
    
    # Get stats
    compression_stats = compressor.get_stats()
    dedup_stats = deduplicator.get_stats()
    
    print(f"Compression stats: {compression_stats}")
    print(f"Deduplication stats: {dedup_stats}")


def main():
    """Run all examples."""
    print("CloudWatch Integration Examples")
    print("=" * 50)
    
    # Set up environment (optional)
    os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Run examples
    basic_cloudwatch_example()
    auto_configuration_example()
    multi_destination_example()
    cost_optimization_example()
    compression_and_deduplication_example()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: CloudWatch examples may fail without proper AWS credentials.")
    print("The examples demonstrate the API usage and configuration options.")


if __name__ == "__main__":
    main()