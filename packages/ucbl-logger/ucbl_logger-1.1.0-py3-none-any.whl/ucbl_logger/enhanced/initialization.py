"""
Comprehensive initialization system for Enhanced EKS Logger

This module provides initialization utilities, validation, and setup
for the enhanced logging system with proper error handling and fallbacks.
"""

import os
import sys
import logging
import traceback
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .config import EnhancedEKSConfig, ConfigurationManager
from .enhanced_eks_logger_impl import EnhancedEKSLogger
from .factory import EnhancedEKSLoggerFactory


class InitializationError(Exception):
    """Exception raised during logger initialization"""
    pass


class LoggerInitializer:
    """
    Comprehensive logger initializer with validation, error handling,
    and graceful degradation capabilities.
    """
    
    def __init__(self):
        self._python_logger = logging.getLogger(__name__)
        self._initialization_log = []
    
    def initialize_logger(self, 
                         config: Optional[EnhancedEKSConfig] = None,
                         service_name: Optional[str] = None,
                         namespace: Optional[str] = None,
                         environment: str = 'auto',
                         validate_config: bool = True,
                         fail_on_validation_errors: bool = False) -> Tuple[EnhancedEKSLogger, Dict[str, Any]]:
        """
        Initialize Enhanced EKS Logger with comprehensive validation and error handling
        
        Args:
            config: Pre-configured EnhancedEKSConfig (optional)
            service_name: Service name override
            namespace: Namespace override
            environment: Target environment ('development', 'staging', 'production', 'auto')
            validate_config: Whether to validate configuration
            fail_on_validation_errors: Whether to fail on validation errors
            
        Returns:
            Tuple of (logger_instance, initialization_report)
            
        Raises:
            InitializationError: If initialization fails critically
        """
        initialization_report = {
            'success': False,
            'config_source': 'unknown',
            'validation_results': {},
            'component_status': {},
            'warnings': [],
            'errors': [],
            'fallbacks_used': []
        }
        
        try:
            # Step 1: Create or validate configuration
            if config is None:
                self._log_step("Creating configuration from environment")
                config = self._create_configuration(environment, service_name, namespace)
                initialization_report['config_source'] = 'environment'
            else:
                self._log_step("Using provided configuration")
                initialization_report['config_source'] = 'provided'
                
                # Apply overrides if provided
                if service_name:
                    config.service_name = service_name
                if namespace:
                    config.namespace = namespace
            
            # Step 2: Validate configuration
            if validate_config:
                self._log_step("Validating configuration")
                validation_results = self._validate_configuration(config)
                initialization_report['validation_results'] = validation_results
                
                if not validation_results['valid'] and fail_on_validation_errors:
                    raise InitializationError(
                        f"Configuration validation failed: {', '.join(validation_results['issues'])}"
                    )
                
                if validation_results['issues']:
                    initialization_report['warnings'].extend(validation_results['issues'])
            
            # Step 3: Check system requirements
            self._log_step("Checking system requirements")
            requirements_check = self._check_system_requirements(config)
            initialization_report['system_requirements'] = requirements_check
            
            if requirements_check['missing_critical']:
                initialization_report['warnings'].append(
                    f"Missing critical requirements: {requirements_check['missing_critical']}"
                )
            
            # Step 4: Initialize logger with graceful degradation
            self._log_step("Initializing Enhanced EKS Logger")
            logger, component_status = self._initialize_logger_with_fallbacks(config)
            initialization_report['component_status'] = component_status
            
            # Step 5: Perform post-initialization validation
            self._log_step("Performing post-initialization validation")
            post_init_results = self._post_initialization_validation(logger)
            initialization_report['post_init_validation'] = post_init_results
            
            # Step 6: Log successful initialization
            self._log_step("Initialization completed successfully")
            initialization_report['success'] = True
            initialization_report['initialization_log'] = self._initialization_log
            
            # Log initialization summary through the new logger
            logger.info("Enhanced EKS Logger initialized successfully", 
                       event_type="logger_initialization",
                       initialization_report=initialization_report)
            
            return logger, initialization_report
            
        except Exception as e:
            error_msg = f"Logger initialization failed: {e}"
            self._python_logger.error(error_msg)
            initialization_report['errors'].append(error_msg)
            initialization_report['exception'] = str(e)
            initialization_report['traceback'] = traceback.format_exc()
            
            # Try to create a minimal fallback logger
            try:
                fallback_logger = self._create_fallback_logger(service_name or 'graphrag-toolkit')
                initialization_report['fallback_created'] = True
                return fallback_logger, initialization_report
            except Exception as fallback_error:
                initialization_report['fallback_error'] = str(fallback_error)
                raise InitializationError(f"Complete initialization failure: {e}") from e
    
    def _create_configuration(self, environment: str, service_name: Optional[str], 
                            namespace: Optional[str]) -> EnhancedEKSConfig:
        """Create configuration based on environment and overrides"""
        try:
            # Create environment-specific configuration
            config = ConfigurationManager.create_for_environment(environment)
            
            # Apply overrides
            if service_name:
                config.service_name = service_name
            if namespace:
                config.namespace = namespace
            
            self._log_step(f"Configuration created for environment: {environment}")
            return config
            
        except Exception as e:
            self._log_step(f"Failed to create configuration: {e}")
            # Fallback to basic configuration
            config = EnhancedEKSConfig()
            if service_name:
                config.service_name = service_name
            if namespace:
                config.namespace = namespace
            return config
    
    def _validate_configuration(self, config: EnhancedEKSConfig) -> Dict[str, Any]:
        """Validate configuration and return detailed results"""
        try:
            return ConfigurationManager.validate_and_suggest_fixes(config)
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Configuration validation failed: {e}"],
                'warnings': [],
                'suggestions': []
            }
    
    def _check_system_requirements(self, config: EnhancedEKSConfig) -> Dict[str, Any]:
        """Check system requirements and dependencies"""
        requirements = {
            'python_version': sys.version_info >= (3, 8),
            'kubernetes_available': self._check_kubernetes_availability(),
            'aws_credentials': self._check_aws_credentials() if config.enable_cloudwatch else True,
            'required_packages': self._check_required_packages(config),
            'missing_critical': [],
            'missing_optional': []
        }
        
        # Check critical requirements
        if not requirements['python_version']:
            requirements['missing_critical'].append('Python 3.8+ required')
        
        if config.enable_cloudwatch and not requirements['aws_credentials']:
            requirements['missing_optional'].append('AWS credentials for CloudWatch')
        
        return requirements
    
    def _check_kubernetes_availability(self) -> bool:
        """Check if running in Kubernetes environment"""
        return (
            os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount') or
            os.getenv('KUBERNETES_SERVICE_HOST') is not None
        )
    
    def _check_aws_credentials(self) -> bool:
        """Check if AWS credentials are available"""
        return (
            os.getenv('AWS_ACCESS_KEY_ID') is not None or
            os.getenv('AWS_PROFILE') is not None or
            os.path.exists(os.path.expanduser('~/.aws/credentials'))
        )
    
    def _check_required_packages(self, config: EnhancedEKSConfig) -> Dict[str, bool]:
        """Check availability of required packages"""
        packages = {}
        
        # Always required
        packages['psutil'] = self._check_package('psutil')
        
        # Conditionally required
        if config.enable_cloudwatch:
            packages['boto3'] = self._check_package('boto3')
        
        if config.otel_endpoint:
            packages['opentelemetry'] = self._check_package('opentelemetry')
        
        return packages
    
    def _check_package(self, package_name: str) -> bool:
        """Check if a package is available"""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    def _initialize_logger_with_fallbacks(self, config: EnhancedEKSConfig) -> Tuple[EnhancedEKSLogger, Dict[str, Any]]:
        """Initialize logger with graceful degradation"""
        component_status = {}
        
        try:
            # Try full initialization
            logger = EnhancedEKSLoggerFactory.create_logger(config)
            
            # Check component status
            component_status = logger.get_component_status()
            
            return logger, component_status
            
        except Exception as e:
            self._log_step(f"Full initialization failed: {e}, trying with reduced features")
            
            # Try with reduced features
            reduced_config = self._create_reduced_config(config)
            try:
                logger = EnhancedEKSLoggerFactory.create_logger(reduced_config)
                component_status = logger.get_component_status()
                component_status['fallback_mode'] = True
                return logger, component_status
            except Exception as e2:
                self._log_step(f"Reduced initialization failed: {e2}")
                raise InitializationError(f"All initialization attempts failed: {e}, {e2}")
    
    def _create_reduced_config(self, config: EnhancedEKSConfig) -> EnhancedEKSConfig:
        """Create configuration with reduced features for fallback"""
        reduced_config = EnhancedEKSConfig(
            service_name=config.service_name,
            namespace=config.namespace,
            log_level=config.log_level,
            enable_tracing=False,  # Disable complex features
            enable_performance_monitoring=False,
            enable_kubernetes_metadata=True,  # Keep basic metadata
            enable_sampling=False,
            enable_security_logging=False,
            enable_health_monitoring=True,  # Keep health monitoring
            enable_cloudwatch=False  # Disable CloudWatch for fallback
        )
        return reduced_config
    
    def _create_fallback_logger(self, service_name: str) -> EnhancedEKSLogger:
        """Create minimal fallback logger"""
        minimal_config = EnhancedEKSConfig(
            service_name=service_name,
            namespace="default",
            enable_tracing=False,
            enable_performance_monitoring=False,
            enable_kubernetes_metadata=False,
            enable_sampling=False,
            enable_security_logging=False,
            enable_health_monitoring=False,
            enable_cloudwatch=False
        )
        
        return EnhancedEKSLogger(
            service_name=minimal_config.service_name,
            namespace=minimal_config.namespace,
            enable_tracing=False,
            enable_performance_monitoring=False,
            enable_kubernetes_metadata=False,
            enable_sampling=False,
            enable_security_logging=False,
            enable_health_monitoring=False,
            enable_cloudwatch=False
        )
    
    def _post_initialization_validation(self, logger: EnhancedEKSLogger) -> Dict[str, Any]:
        """Perform post-initialization validation"""
        results = {
            'health_check': False,
            'basic_logging': False,
            'component_status': {},
            'errors': []
        }
        
        try:
            # Test basic logging
            logger.info("Post-initialization validation test")
            results['basic_logging'] = True
        except Exception as e:
            results['errors'].append(f"Basic logging test failed: {e}")
        
        try:
            # Test health check
            health_status = logger.get_health_status()
            results['health_check'] = True
            results['health_status'] = health_status.__dict__ if hasattr(health_status, '__dict__') else str(health_status)
        except Exception as e:
            results['errors'].append(f"Health check test failed: {e}")
        
        try:
            # Get component status
            results['component_status'] = logger.get_component_status()
        except Exception as e:
            results['errors'].append(f"Component status check failed: {e}")
        
        return results
    
    def _log_step(self, message: str) -> None:
        """Log initialization step"""
        self._initialization_log.append(message)
        self._python_logger.debug(f"Logger initialization: {message}")


def initialize_enhanced_logger(service_name: Optional[str] = None,
                             namespace: Optional[str] = None,
                             config_file: Optional[str] = None,
                             environment: str = 'auto',
                             validate_config: bool = True) -> Tuple[EnhancedEKSLogger, Dict[str, Any]]:
    """
    Convenience function to initialize Enhanced EKS Logger
    
    Args:
        service_name: Service name (defaults to environment variable or 'graphrag-toolkit')
        namespace: Kubernetes namespace (defaults to environment variable or 'default')
        config_file: Path to configuration file (optional)
        environment: Target environment ('development', 'staging', 'production', 'auto')
        validate_config: Whether to validate configuration
        
    Returns:
        Tuple of (logger_instance, initialization_report)
    """
    initializer = LoggerInitializer()
    
    # Load configuration from file if provided
    config = None
    if config_file:
        try:
            config = EnhancedEKSConfig.from_file(config_file)
        except Exception as e:
            # Log error but continue with environment-based config
            logging.getLogger(__name__).warning(f"Failed to load config file {config_file}: {e}")
    
    return initializer.initialize_logger(
        config=config,
        service_name=service_name,
        namespace=namespace,
        environment=environment,
        validate_config=validate_config
    )


def quick_setup(service_name: str = "graphrag-toolkit", 
               environment: str = 'auto') -> EnhancedEKSLogger:
    """
    Quick setup for Enhanced EKS Logger with minimal configuration
    
    Args:
        service_name: Service name
        environment: Target environment
        
    Returns:
        EnhancedEKSLogger instance
    """
    logger, report = initialize_enhanced_logger(
        service_name=service_name,
        environment=environment,
        validate_config=False  # Skip validation for quick setup
    )
    
    if not report['success']:
        logging.getLogger(__name__).warning(
            f"Quick setup completed with issues: {report.get('warnings', [])}"
        )
    
    return logger