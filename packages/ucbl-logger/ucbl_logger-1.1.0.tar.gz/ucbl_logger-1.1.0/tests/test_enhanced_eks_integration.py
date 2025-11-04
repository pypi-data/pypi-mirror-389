"""
Comprehensive integration tests for Enhanced EKS Logger

This module tests the complete enhanced logging system including:
- End-to-end logging pipeline with all components enabled
- Backward compatibility with existing UCBLLogger usage patterns
- Configuration management, feature flags, and graceful degradation
"""

import os
import json
import time
import tempfile
import threading
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from ucbl_logger import UCBLLogger, LogLevel
from ucbl_logger.enhanced import (
    EnhancedEKSLogger,
    EnhancedEKSConfig,
    ConfigurationManager,
    initialize_enhanced_logger,
    quick_setup,
    InitializationError
)


class TestEnhancedEKSIntegration:
    """Test complete Enhanced EKS Logger integration"""
    
    def test_end_to_end_logging_pipeline_all_components(self):
        """Test end-to-end logging pipeline with all components enabled"""
        # Create configuration with all features enabled
        config = EnhancedEKSConfig(
            service_name="test-service",
            namespace="test-namespace",
            enable_tracing=True,
            enable_performance_monitoring=True,
            enable_kubernetes_metadata=True,
            enable_sampling=True,
            enable_security_logging=True,
            enable_health_monitoring=True,
            enable_cloudwatch=False  # Disable for testing
        )
        
        # Initialize logger
        logger = EnhancedEKSLogger(
            service_name=config.service_name,
            namespace=config.namespace,
            enable_tracing=config.enable_tracing,
            enable_performance_monitoring=config.enable_performance_monitoring,
            enable_kubernetes_metadata=config.enable_kubernetes_metadata,
            enable_sampling=config.enable_sampling,
            enable_security_logging=config.enable_security_logging,
            enable_health_monitoring=config.enable_health_monitoring,
            enable_cloudwatch=config.enable_cloudwatch
        )
        
        # Test basic logging
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.critical("Test critical message")
        
        # Test tracing
        correlation_id = logger.start_trace("test_operation")
        assert correlation_id is not None
        logger.info("Operation in progress", correlation_id=correlation_id)
        logger.end_trace(correlation_id, success=True)
        
        # Test performance monitoring
        logger.log_performance_metrics()
        
        # Test health status
        health_status = logger.get_health_status()
        assert health_status is not None
        
        # Test component status
        component_status = logger.get_component_status()
        assert component_status['initialized'] is True
        
        # Cleanup
        logger.shutdown()
    
    def test_backward_compatibility_ucbl_logger(self):
        """Test complete backward compatibility with existing UCBLLogger usage patterns"""
        # Test original constructor patterns
        logger1 = UCBLLogger()
        logger2 = UCBLLogger(log_level=None)
        logger3 = UCBLLogger(log_level=LogLevel.DEBUG, timezone_str='UTC')
        
        # Test all original methods work
        for logger in [logger1, logger2, logger3]:
            # Basic logging methods
            logger.info("Test info")
            logger.debug("Test debug")
            logger.warning("Test warning")
            logger.error("Test error")
            logger.critical("Test critical")
            
            # Task logging methods
            logger.log_task_start("test_task")
            logger.log_task_stop("test_task")
            
            # Risk logging methods
            logger.log_risk("Test risk")
            logger.log_anomaly("Test anomaly")
            
            # Legacy methods
            logger.log_suspicious_activity("Test suspicious")
            logger.log_step_start("test_step")
            logger.log_step_stop("test_step")
    
    def test_enhanced_features_with_backward_compatibility(self):
        """Test enhanced features work alongside backward compatibility"""
        # Create logger with enhanced features
        logger = UCBLLogger(
            service_name="test-service",
            enable_eks_features=True
        )
        
        # Test backward compatible methods still work
        logger.info("Basic info message")
        logger.log_task_start("test_task")
        logger.log_task_stop("test_task")
        
        # Test enhanced methods work if available
        if logger.is_enhanced_mode():
            correlation_id = logger.start_trace("test_operation")
            if correlation_id:
                logger.info("Enhanced info message", correlation_id=correlation_id)
                logger.end_trace(correlation_id)
            
            logger.log_performance_metrics()
            health_status = logger.get_health_status()
            assert health_status is not None
    
    def test_configuration_management_comprehensive(self):
        """Test comprehensive configuration management"""
        # Test environment-based configuration
        with patch.dict(os.environ, {
            'UCBL_SERVICE_NAME': 'env-test-service',
            'KUBERNETES_NAMESPACE': 'env-test-namespace',
            'UCBL_ENABLE_TRACING': 'true',
            'UCBL_ENABLE_SAMPLING': 'false',
            'UCBL_LOG_LEVEL': 'DEBUG'
        }):
            config = EnhancedEKSConfig.from_environment()
            assert config.service_name == 'env-test-service'
            assert config.namespace == 'env-test-namespace'
            assert config.enable_tracing is True
            assert config.enable_sampling is False
            assert config.log_level == 'DEBUG'
        
        # Test configuration validation
        issues = config.validate()
        assert isinstance(issues, list)
        
        # Test configuration file loading
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_dict = {
                'service_name': 'file-test-service',
                'namespace': 'file-test-namespace',
                'features': {
                    'tracing': True,
                    'sampling': False
                }
            }
            json.dump(config_dict, f)
            f.flush()
            
            file_config = EnhancedEKSConfig.from_file(f.name)
            assert file_config.service_name == 'file-test-service'
            assert file_config.namespace == 'file-test-namespace'
            assert file_config.enable_tracing is True
            assert file_config.enable_sampling is False
            
            os.unlink(f.name)
    
    def test_feature_flags_and_gradual_rollout(self):
        """Test feature flags and gradual rollout capabilities"""
        # Test individual feature flags
        feature_flags = {
            'tracing': True,
            'performance_monitoring': False,
            'sampling': True,
            'security_logging': False
        }
        
        logger = UCBLLogger.create_with_feature_flags(
            service_name="feature-test-service",
            feature_flags=feature_flags
        )
        
        # Verify feature flags are respected
        if logger.is_enhanced_mode():
            component_status = logger.get_component_status()
            components = component_status.get('components', {})
            
            # Check that enabled features are available
            if 'tracing' in components:
                assert components['tracing']['enabled'] is True
            if 'sampling' in components:
                assert components['sampling']['enabled'] is True
        
        # Test environment-specific configuration
        for environment in ['development', 'staging', 'production']:
            env_logger = UCBLLogger.create_for_environment(
                service_name=f"{environment}-service",
                environment=environment
            )
            
            logger_info = env_logger.get_logger_info()
            assert logger_info['service_name'] == f"{environment}-service"
    
    def test_graceful_degradation_scenarios(self):
        """Test graceful degradation under various failure scenarios"""
        # Test with missing dependencies
        with patch('ucbl_logger.enhanced.enhanced_eks_logger_impl.BaseTracingManager') as mock_tracing:
            mock_tracing.side_effect = ImportError("Missing dependency")
            
            logger = EnhancedEKSLogger(
                service_name="degradation-test",
                enable_tracing=True
            )
            
            # Logger should still work with degraded functionality
            logger.info("Test message during degradation")
            component_status = logger.get_component_status()
            assert component_status['initialized'] is True
        
        # Test with invalid configuration
        invalid_config = EnhancedEKSConfig(
            service_name="",  # Invalid empty service name
            namespace="",     # Invalid empty namespace
        )
        
        issues = invalid_config.validate()
        assert len(issues) > 0
        
        # Logger should still initialize with fallback values
        try:
            logger = EnhancedEKSLogger(
                service_name=invalid_config.service_name or "fallback-service",
                namespace=invalid_config.namespace or "default"
            )
            logger.info("Test with fallback configuration")
        except Exception as e:
            pytest.fail(f"Logger should handle invalid config gracefully: {e}")
    
    def test_initialization_system_comprehensive(self):
        """Test comprehensive initialization system"""
        # Test successful initialization
        logger, report = initialize_enhanced_logger(
            service_name="init-test-service",
            environment='development',
            validate_config=True
        )
        
        assert report['success'] is True
        assert logger is not None
        assert report['config_source'] in ['environment', 'provided']
        
        # Test initialization with validation errors (non-fatal)
        with patch.dict(os.environ, {
            'UCBL_SAMPLING_DEFAULT_RATE': '2.0'  # Invalid rate > 1.0
        }):
            logger, report = initialize_enhanced_logger(
                service_name="validation-test-service",
                validate_config=True
            )
            
            # Should still succeed but with warnings
            assert logger is not None
            assert len(report.get('warnings', [])) > 0
        
        # Test quick setup
        quick_logger = quick_setup(service_name="quick-test-service")
        assert quick_logger is not None
        
        quick_logger.info("Quick setup test message")
    
    def test_concurrent_logging_thread_safety(self):
        """Test thread safety under concurrent logging"""
        logger = EnhancedEKSLogger(
            service_name="concurrent-test",
            enable_tracing=True,
            enable_sampling=False  # Disable sampling for predictable behavior
        )
        
        results = []
        errors = []
        
        def log_worker(worker_id: int, message_count: int):
            try:
                for i in range(message_count):
                    correlation_id = logger.start_trace(f"worker_{worker_id}_operation_{i}")
                    logger.info(f"Worker {worker_id} message {i}", correlation_id=correlation_id)
                    logger.end_trace(correlation_id, success=True)
                    time.sleep(0.001)  # Small delay to encourage race conditions
                results.append(f"Worker {worker_id} completed")
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        # Start multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=log_worker, args=(worker_id, 10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent logging errors: {errors}"
        assert len(results) == 5, f"Expected 5 workers to complete, got {len(results)}"
        
        logger.shutdown()
    
    def test_performance_under_load(self):
        """Test performance characteristics under load"""
        logger = EnhancedEKSLogger(
            service_name="performance-test",
            enable_sampling=True,  # Enable sampling to test volume handling
            enable_performance_monitoring=True
        )
        
        # Configure aggressive sampling for load test
        logger.configure_sampling({
            'default_rate': 0.1,  # Sample 10% of logs
            'volume_threshold': 100
        })
        
        start_time = time.time()
        message_count = 1000
        
        # Log many messages quickly
        for i in range(message_count):
            logger.info(f"Load test message {i}", test_iteration=i)
            
            # Periodically log performance metrics
            if i % 100 == 0:
                logger.log_performance_metrics()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify reasonable performance (should handle 1000 messages in reasonable time)
        assert duration < 10.0, f"Load test took too long: {duration} seconds"
        
        # Verify logger is still healthy after load
        health_status = logger.get_health_status()
        assert health_status is not None
        
        logger.shutdown()
    
    def test_configuration_validation_comprehensive(self):
        """Test comprehensive configuration validation"""
        # Test valid configuration
        valid_config = EnhancedEKSConfig(
            service_name="valid-service",
            namespace="valid-namespace",
            log_level="INFO"
        )
        
        issues = valid_config.validate()
        assert len(issues) == 0
        
        # Test invalid configurations
        invalid_configs = [
            # Empty service name
            EnhancedEKSConfig(service_name="", namespace="test"),
            # Invalid log level
            EnhancedEKSConfig(service_name="test", log_level="INVALID"),
            # Invalid sampling rate
            EnhancedEKSConfig(service_name="test", sampling_config=MagicMock(default_rate=2.0)),
        ]
        
        for config in invalid_configs:
            issues = config.validate()
            assert len(issues) > 0
        
        # Test configuration suggestions
        validation_results = ConfigurationManager.validate_and_suggest_fixes(valid_config)
        assert validation_results['valid'] is True
        assert 'suggestions' in validation_results
        assert 'environment_variables' in validation_results
    
    def test_environment_detection_and_optimization(self):
        """Test environment detection and optimization"""
        # Test development environment
        dev_config = ConfigurationManager.create_for_environment('development')
        assert dev_config.log_level == 'DEBUG'
        assert dev_config.enable_sampling is False
        
        # Test production environment
        prod_config = ConfigurationManager.create_for_environment('production')
        assert prod_config.log_level == 'INFO'
        assert prod_config.enable_sampling is True
        if prod_config.sampling_config:
            assert prod_config.sampling_config.default_rate <= 0.1
        
        # Test auto-detection with mocked environment
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'KUBERNETES_NAMESPACE': 'prod-namespace'
        }):
            auto_config = ConfigurationManager.create_for_environment('auto')
            # Should detect production environment
            assert auto_config.enable_sampling is True
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        # Test initialization with missing components
        with patch('ucbl_logger.enhanced.enhanced_eks_logger_impl.KubernetesMetadataCollector') as mock_k8s:
            mock_k8s.side_effect = Exception("Kubernetes API unavailable")
            
            logger, report = initialize_enhanced_logger(
                service_name="error-test-service",
                validate_config=False
            )
            
            # Should still initialize with degraded functionality
            assert logger is not None
            assert len(report.get('warnings', [])) > 0 or len(report.get('errors', [])) > 0
        
        # Test logging continues during component failures
        logger = EnhancedEKSLogger(
            service_name="recovery-test",
            enable_performance_monitoring=True
        )
        
        # Mock performance monitor to fail
        if logger._performance_monitor:
            with patch.object(logger._performance_monitor, 'get_current_metrics') as mock_metrics:
                mock_metrics.side_effect = Exception("Performance monitoring failed")
                
                # Logging should continue despite performance monitoring failure
                logger.info("Test message during performance monitoring failure")
                logger.log_performance_metrics()  # Should not raise exception
        
        logger.shutdown()


class TestBackwardCompatibilityComplete:
    """Comprehensive backward compatibility tests"""
    
    def test_all_original_constructor_patterns(self):
        """Test all original UCBLLogger constructor patterns"""
        # Test various constructor patterns that existed
        loggers = [
            UCBLLogger(),
            UCBLLogger(log_level=None),
            UCBLLogger(timezone_str='UTC'),
            UCBLLogger(log_level=LogLevel.DEBUG),
            UCBLLogger(log_level=LogLevel.INFO, timezone_str='America/New_York'),
        ]
        
        for logger in loggers:
            # All should initialize without error
            assert logger is not None
            logger.info("Backward compatibility test")
    
    def test_all_original_logging_methods(self):
        """Test all original logging methods work identically"""
        logger = UCBLLogger()
        
        # Test all basic logging methods
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.critical("Test critical message")
        
        # Test task logging methods
        logger.log_task_start("test_task")
        logger.log_task_start("test_task", "CustomType")
        logger.log_task_stop("test_task")
        
        # Test risk logging methods
        logger.log_risk("Test risk message")
        logger.log_risk("Critical risk", critical=True)
        logger.log_risk("Minor risk", minor=True)
        logger.log_anomaly("Test anomaly")
        
        # Test legacy methods
        logger.log_suspicious_activity("Suspicious activity")
        logger.log_step_start("test_step")
        logger.log_step_stop("test_step")
    
    def test_method_signatures_unchanged(self):
        """Test that method signatures remain unchanged for backward compatibility"""
        logger = UCBLLogger()
        
        # Test methods can be called with original signatures
        logger.info("message")
        logger.log_task_start("task")
        logger.log_task_start("task", "type")
        logger.log_task_stop("task")
        logger.log_risk("risk")
        logger.log_risk("risk", critical=True)
        logger.log_risk("risk", minor=True)
        logger.log_anomaly("anomaly")
        
        # Test methods also accept new optional parameters without breaking
        logger.info("message", extra_param="value")
        logger.log_task_start("task", correlation_id="test-id")
    
    def test_enhanced_features_optional(self):
        """Test that enhanced features are completely optional"""
        # Test logger works without any enhanced features
        with patch('ucbl_logger.logger._enhanced_available', False):
            logger = UCBLLogger()
            
            # All original functionality should work
            logger.info("Test without enhanced features")
            logger.log_task_start("test_task")
            logger.log_task_stop("test_task")
            
            # Enhanced methods should return None or do nothing gracefully
            assert logger.start_trace("operation") is None
            logger.end_trace("dummy_id")  # Should not raise error
            logger.log_performance_metrics()  # Should not raise error
            assert logger.get_health_status() is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])