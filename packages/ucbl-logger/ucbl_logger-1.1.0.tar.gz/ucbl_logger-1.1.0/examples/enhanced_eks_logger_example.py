#!/usr/bin/env python3
"""
Enhanced EKS Logger Example

This example demonstrates the complete Enhanced EKS Logger functionality
including backward compatibility, enhanced features, and configuration options.
"""

import os
import time
from ucbl_logger import UCBLLogger
from ucbl_logger.enhanced import (
    EnhancedEKSLogger,
    EnhancedEKSConfig,
    ConfigurationManager,
    initialize_enhanced_logger,
    quick_setup
)


def demonstrate_backward_compatibility():
    """Demonstrate complete backward compatibility"""
    print("\n=== Backward Compatibility Demo ===")
    
    # Original UCBLLogger usage patterns still work
    logger = UCBLLogger()
    
    print("Testing original logging methods...")
    logger.info("This is an info message (backward compatible)")
    logger.debug("This is a debug message (backward compatible)")
    logger.warning("This is a warning message (backward compatible)")
    logger.error("This is an error message (backward compatible)")
    
    print("Testing original task logging...")
    logger.log_task_start("example_task")
    logger.info("Task is running...")
    logger.log_task_stop("example_task")
    
    print("Testing original risk logging...")
    logger.log_risk("Example risk detected")
    logger.log_anomaly("Example anomaly detected")
    
    print("Backward compatibility demo completed!")


def demonstrate_enhanced_features():
    """Demonstrate enhanced EKS features"""
    print("\n=== Enhanced Features Demo ===")
    
    # Create logger with enhanced features
    logger = UCBLLogger(
        service_name="demo-service",
        enable_eks_features=True
    )
    
    if logger.is_enhanced_mode():
        print("Enhanced mode is enabled!")
        
        # Demonstrate distributed tracing
        print("Testing distributed tracing...")
        correlation_id = logger.start_trace("demo_operation")
        logger.info("Operation started", correlation_id=correlation_id)
        time.sleep(0.1)  # Simulate work
        logger.info("Operation in progress", correlation_id=correlation_id)
        logger.end_trace(correlation_id, success=True)
        
        # Demonstrate performance monitoring
        print("Testing performance monitoring...")
        logger.log_performance_metrics()
        
        # Demonstrate health monitoring
        print("Testing health monitoring...")
        health_status = logger.get_health_status()
        if health_status:
            print(f"Logger health status: {health_status}")
        
        # Demonstrate enhanced task logging with tracing
        print("Testing enhanced task logging...")
        task_correlation_id = logger.log_task_start("enhanced_task", "Demo")
        logger.info("Enhanced task is running", correlation_id=task_correlation_id)
        logger.log_task_stop("enhanced_task", correlation_id=task_correlation_id, success=True)
        
        # Get component status
        component_status = logger.get_component_status()
        print(f"Component status: {component_status}")
        
    else:
        print("Enhanced mode is not available, using standard logging")
        logger.info("Standard logging message")
    
    print("Enhanced features demo completed!")


def demonstrate_configuration_management():
    """Demonstrate configuration management"""
    print("\n=== Configuration Management Demo ===")
    
    # Create configuration for different environments
    print("Creating development configuration...")
    dev_config = ConfigurationManager.create_for_environment('development')
    print(f"Development config - Log level: {dev_config.log_level}, Sampling: {dev_config.enable_sampling}")
    
    print("Creating production configuration...")
    prod_config = ConfigurationManager.create_for_environment('production')
    print(f"Production config - Log level: {prod_config.log_level}, Sampling: {prod_config.enable_sampling}")
    
    # Demonstrate configuration validation
    print("Validating configuration...")
    validation_results = ConfigurationManager.validate_and_suggest_fixes(dev_config)
    print(f"Configuration valid: {validation_results['valid']}")
    if validation_results['suggestions']:
        print(f"Suggestions: {validation_results['suggestions']}")
    
    # Create logger with specific configuration
    logger = EnhancedEKSLogger(
        service_name="config-demo-service",
        namespace="demo-namespace",
        enable_tracing=True,
        enable_performance_monitoring=True,
        enable_sampling=False  # Disable for demo
    )
    
    logger.info("Configuration demo message")
    logger.shutdown()
    
    print("Configuration management demo completed!")


def demonstrate_feature_flags():
    """Demonstrate feature flags and gradual rollout"""
    print("\n=== Feature Flags Demo ===")
    
    # Create logger with specific feature flags
    feature_flags = {
        'tracing': True,
        'performance_monitoring': False,
        'sampling': True,
        'security_logging': False
    }
    
    logger = UCBLLogger.create_with_feature_flags(
        service_name="feature-flag-demo",
        feature_flags=feature_flags
    )
    
    print(f"Logger info: {logger.get_logger_info()}")
    
    # Test features based on flags
    if logger.is_enhanced_mode():
        correlation_id = logger.start_trace("feature_test")
        logger.info("Testing with feature flags", correlation_id=correlation_id)
        logger.end_trace(correlation_id)
    
    logger.info("Feature flags demo message")
    print("Feature flags demo completed!")


def demonstrate_initialization_system():
    """Demonstrate comprehensive initialization system"""
    print("\n=== Initialization System Demo ===")
    
    # Quick setup for simple use cases
    print("Testing quick setup...")
    quick_logger = quick_setup(service_name="quick-demo-service")
    quick_logger.info("Quick setup message")
    
    # Comprehensive initialization with validation
    print("Testing comprehensive initialization...")
    logger, report = initialize_enhanced_logger(
        service_name="init-demo-service",
        environment='development',
        validate_config=True
    )
    
    print(f"Initialization successful: {report['success']}")
    print(f"Configuration source: {report['config_source']}")
    if report.get('warnings'):
        print(f"Warnings: {report['warnings']}")
    
    logger.info("Comprehensive initialization message")
    
    print("Initialization system demo completed!")


def demonstrate_error_handling():
    """Demonstrate graceful error handling and degradation"""
    print("\n=== Error Handling Demo ===")
    
    # Test with invalid configuration (should handle gracefully)
    try:
        config = EnhancedEKSConfig(
            service_name="error-demo",
            namespace="demo"
        )
        
        # Validate configuration
        issues = config.validate()
        if issues:
            print(f"Configuration issues (handled gracefully): {issues}")
        
        # Logger should still work
        logger = EnhancedEKSLogger(
            service_name=config.service_name,
            namespace=config.namespace,
            enable_cloudwatch=False  # Disable to avoid AWS dependency
        )
        
        logger.info("Error handling demo - logger works despite issues")
        logger.shutdown()
        
    except Exception as e:
        print(f"Error handled gracefully: {e}")
    
    print("Error handling demo completed!")


def main():
    """Run all demonstrations"""
    print("Enhanced EKS Logger Demonstration")
    print("=" * 50)
    
    # Set up environment for demo
    os.environ['UCBL_SERVICE_NAME'] = 'demo-service'
    os.environ['UCBL_LOG_LEVEL'] = 'INFO'
    
    try:
        demonstrate_backward_compatibility()
        demonstrate_enhanced_features()
        demonstrate_configuration_management()
        demonstrate_feature_flags()
        demonstrate_initialization_system()
        demonstrate_error_handling()
        
        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()