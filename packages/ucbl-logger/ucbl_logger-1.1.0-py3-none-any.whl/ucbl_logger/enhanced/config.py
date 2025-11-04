"""
Configuration management for enhanced EKS logging components

This module provides configuration classes and utilities for managing
the enhanced logging system configuration with comprehensive validation
and environment variable support.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
from .sampling.models import SamplingConfig
from .buffering.models import BufferConfig
from .performance.models import PerformanceThresholds


@dataclass
class EnhancedEKSConfig:
    """
    Complete configuration for Enhanced EKS Logger with comprehensive validation
    and environment variable support optimized for container deployment.
    """
    
    # Basic configuration
    service_name: str = "graphrag-toolkit"
    namespace: str = "default"
    log_level: str = "INFO"
    
    # Feature flags
    enable_tracing: bool = True
    enable_performance_monitoring: bool = True
    enable_kubernetes_metadata: bool = True
    enable_sampling: bool = True
    enable_security_logging: bool = True
    enable_health_monitoring: bool = True
    enable_cloudwatch: bool = True
    
    # Component configurations
    sampling_config: SamplingConfig = field(default_factory=SamplingConfig)
    buffer_config: BufferConfig = field(default_factory=BufferConfig)
    performance_thresholds: PerformanceThresholds = field(default_factory=PerformanceThresholds)
    
    # CloudWatch configuration
    cloudwatch_log_group: Optional[str] = None
    cloudwatch_log_stream: Optional[str] = None
    cloudwatch_region: Optional[str] = None
    cloudwatch_batch_size: int = 100
    cloudwatch_flush_interval: int = 5
    
    # OpenTelemetry configuration
    otel_endpoint: Optional[str] = None
    otel_service_name: Optional[str] = None
    otel_service_version: Optional[str] = None
    otel_headers: Optional[Dict[str, str]] = None
    
    # Security configuration
    enable_data_redaction: bool = True
    redaction_patterns: List[str] = field(default_factory=lambda: [
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'(?i)(password|token|key|secret)[\s]*[:=][\s]*[^\s]+',  # Secrets
    ])
    
    # Health monitoring configuration
    health_check_interval: int = 30
    health_endpoint_port: int = 8080
    health_endpoint_path: str = "/health"
    
    # Advanced configuration
    max_log_size_bytes: int = 1024 * 1024  # 1MB
    enable_structured_logging: bool = True
    timezone: str = "UTC"
    
    # Configuration file paths
    config_file_path: Optional[str] = None
    secrets_file_path: Optional[str] = None
    
    @classmethod
    def from_environment(cls) -> 'EnhancedEKSConfig':
        """
        Create configuration from environment variables with comprehensive support
        for container deployment scenarios.
        """
        config = cls()
        
        # Basic configuration from environment
        config.service_name = os.getenv('UCBL_SERVICE_NAME', 
                                      os.getenv('SERVICE_NAME', config.service_name))
        config.namespace = os.getenv('KUBERNETES_NAMESPACE', 
                                   os.getenv('UCBL_NAMESPACE', 
                                           os.getenv('NAMESPACE', config.namespace)))
        config.log_level = os.getenv('UCBL_LOG_LEVEL', 
                                   os.getenv('LOG_LEVEL', config.log_level))
        
        # Feature flags from environment
        config.enable_tracing = _get_bool_env('UCBL_ENABLE_TRACING', config.enable_tracing)
        config.enable_performance_monitoring = _get_bool_env('UCBL_ENABLE_PERFORMANCE', 
                                                           config.enable_performance_monitoring)
        config.enable_kubernetes_metadata = _get_bool_env('UCBL_ENABLE_K8S_METADATA', 
                                                         config.enable_kubernetes_metadata)
        config.enable_sampling = _get_bool_env('UCBL_ENABLE_SAMPLING', config.enable_sampling)
        config.enable_security_logging = _get_bool_env('UCBL_ENABLE_SECURITY', 
                                                      config.enable_security_logging)
        config.enable_health_monitoring = _get_bool_env('UCBL_ENABLE_HEALTH', 
                                                       config.enable_health_monitoring)
        config.enable_cloudwatch = _get_bool_env('UCBL_ENABLE_CLOUDWATCH', config.enable_cloudwatch)
        
        # Sampling configuration from environment
        if config.enable_sampling:
            sampling_config = SamplingConfig()
            sampling_config.enabled = _get_bool_env('UCBL_SAMPLING_ENABLED', True)
            sampling_config.default_rate = _get_float_env('UCBL_SAMPLING_DEFAULT_RATE', 1.0)
            sampling_config.volume_threshold = _get_int_env('UCBL_SAMPLING_VOLUME_THRESHOLD', 1000)
            sampling_config.window_size_seconds = _get_int_env('UCBL_SAMPLING_WINDOW_SIZE', 60)
            sampling_config.preserve_errors = _get_bool_env('UCBL_SAMPLING_PRESERVE_ERRORS', True)
            sampling_config.debug_mode = _get_bool_env('UCBL_SAMPLING_DEBUG_MODE', False)
            
            # Level-specific rates from environment
            level_rates = {}
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                rate = _get_float_env(f'UCBL_SAMPLING_RATE_{level}', None)
                if rate is not None:
                    level_rates[level] = rate
            if level_rates:
                sampling_config.level_rates = level_rates
            
            config.sampling_config = sampling_config
        
        # Buffer configuration from environment
        buffer_config = BufferConfig()
        buffer_config.max_size = _get_int_env('UCBL_BUFFER_MAX_SIZE', 10000)
        buffer_config.flush_interval_seconds = _get_int_env('UCBL_BUFFER_FLUSH_INTERVAL', 5)
        buffer_config.max_retry_attempts = _get_int_env('UCBL_BUFFER_MAX_RETRIES', 3)
        buffer_config.retry_backoff_multiplier = _get_float_env('UCBL_BUFFER_BACKOFF_MULTIPLIER', 2.0)
        buffer_config.enable_compression = _get_bool_env('UCBL_BUFFER_COMPRESSION', True)
        buffer_config.batch_size = _get_int_env('UCBL_BUFFER_BATCH_SIZE', 100)
        config.buffer_config = buffer_config
        
        # Performance thresholds from environment
        thresholds = PerformanceThresholds()
        thresholds.cpu_warning_percent = _get_float_env('UCBL_CPU_WARNING_THRESHOLD', 80.0)
        thresholds.cpu_critical_percent = _get_float_env('UCBL_CPU_CRITICAL_THRESHOLD', 95.0)
        thresholds.memory_warning_percent = _get_float_env('UCBL_MEMORY_WARNING_THRESHOLD', 80.0)
        thresholds.memory_critical_percent = _get_float_env('UCBL_MEMORY_CRITICAL_THRESHOLD', 95.0)
        config.performance_thresholds = thresholds
        
        # CloudWatch configuration from environment
        config.cloudwatch_log_group = os.getenv('UCBL_CLOUDWATCH_LOG_GROUP', 
                                               os.getenv('AWS_LOGS_GROUP'))
        config.cloudwatch_log_stream = os.getenv('UCBL_CLOUDWATCH_LOG_STREAM',
                                                os.getenv('AWS_LOGS_STREAM'))
        config.cloudwatch_region = os.getenv('AWS_REGION', 
                                            os.getenv('UCBL_CLOUDWATCH_REGION',
                                                    os.getenv('AWS_DEFAULT_REGION')))
        config.cloudwatch_batch_size = _get_int_env('UCBL_CLOUDWATCH_BATCH_SIZE', 100)
        config.cloudwatch_flush_interval = _get_int_env('UCBL_CLOUDWATCH_FLUSH_INTERVAL', 5)
        
        # OpenTelemetry configuration from environment
        config.otel_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 
                                       os.getenv('UCBL_OTEL_ENDPOINT'))
        config.otel_service_name = os.getenv('OTEL_SERVICE_NAME', 
                                           os.getenv('UCBL_OTEL_SERVICE_NAME', config.service_name))
        config.otel_service_version = os.getenv('OTEL_SERVICE_VERSION', 
                                              os.getenv('UCBL_OTEL_SERVICE_VERSION'))
        
        # Parse OTEL headers from environment
        otel_headers_str = os.getenv('OTEL_EXPORTER_OTLP_HEADERS', 
                                   os.getenv('UCBL_OTEL_HEADERS'))
        if otel_headers_str:
            try:
                # Parse headers in format "key1=value1,key2=value2"
                headers = {}
                for header_pair in otel_headers_str.split(','):
                    if '=' in header_pair:
                        key, value = header_pair.split('=', 1)
                        headers[key.strip()] = value.strip()
                config.otel_headers = headers
            except Exception:
                pass  # Ignore malformed headers
        
        # Security configuration from environment
        config.enable_data_redaction = _get_bool_env('UCBL_ENABLE_DATA_REDACTION', 
                                                    config.enable_data_redaction)
        
        # Custom redaction patterns from environment
        custom_patterns = os.getenv('UCBL_REDACTION_PATTERNS')
        if custom_patterns:
            try:
                # Parse JSON array of patterns
                patterns = json.loads(custom_patterns)
                if isinstance(patterns, list):
                    config.redaction_patterns.extend(patterns)
            except json.JSONDecodeError:
                # Try comma-separated patterns
                patterns = [p.strip() for p in custom_patterns.split(',') if p.strip()]
                config.redaction_patterns.extend(patterns)
        
        # Health monitoring configuration from environment
        config.health_check_interval = _get_int_env('UCBL_HEALTH_CHECK_INTERVAL', 
                                                  config.health_check_interval)
        config.health_endpoint_port = _get_int_env('UCBL_HEALTH_PORT', 
                                                 os.getenv('PORT', config.health_endpoint_port))
        config.health_endpoint_path = os.getenv('UCBL_HEALTH_PATH', config.health_endpoint_path)
        
        # Advanced configuration from environment
        config.max_log_size_bytes = _get_int_env('UCBL_MAX_LOG_SIZE_BYTES', config.max_log_size_bytes)
        config.enable_structured_logging = _get_bool_env('UCBL_STRUCTURED_LOGGING', 
                                                       config.enable_structured_logging)
        config.timezone = os.getenv('UCBL_TIMEZONE', os.getenv('TZ', config.timezone))
        
        # Configuration file paths from environment
        config.config_file_path = os.getenv('UCBL_CONFIG_FILE')
        config.secrets_file_path = os.getenv('UCBL_SECRETS_FILE')
        
        # Load from configuration file if specified
        if config.config_file_path:
            config = config.merge_from_file(config.config_file_path)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'service_name': self.service_name,
            'namespace': self.namespace,
            'features': {
                'tracing': self.enable_tracing,
                'performance_monitoring': self.enable_performance_monitoring,
                'kubernetes_metadata': self.enable_kubernetes_metadata,
                'sampling': self.enable_sampling,
                'security_logging': self.enable_security_logging,
                'health_monitoring': self.enable_health_monitoring
            },
            'sampling_config': self.sampling_config.__dict__ if self.sampling_config else None,
            'buffer_config': self.buffer_config.__dict__ if self.buffer_config else None,
            'performance_thresholds': self.performance_thresholds.__dict__ if self.performance_thresholds else None,
            'cloudwatch': {
                'log_group': self.cloudwatch_log_group,
                'log_stream': self.cloudwatch_log_stream,
                'region': self.cloudwatch_region
            },
            'opentelemetry': {
                'endpoint': self.otel_endpoint,
                'service_name': self.otel_service_name,
                'service_version': self.otel_service_version
            }
        }
    
    def validate(self) -> List[str]:
        """
        Comprehensive validation of configuration with helpful error messages
        and configuration suggestions.
        """
        issues = []
        
        # Basic configuration validation
        if not self.service_name:
            issues.append("service_name is required. Set UCBL_SERVICE_NAME environment variable.")
        elif not self.service_name.replace('-', '').replace('_', '').isalnum():
            issues.append("service_name must contain only alphanumeric characters, hyphens, and underscores")
        
        if not self.namespace:
            issues.append("namespace is required. Set KUBERNETES_NAMESPACE environment variable.")
        elif not self.namespace.replace('-', '').isalnum():
            issues.append("namespace must contain only alphanumeric characters and hyphens")
        
        # Log level validation
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            issues.append(f"log_level must be one of {valid_log_levels}. Current: {self.log_level}")
        
        # Sampling configuration validation
        if self.enable_sampling and self.sampling_config:
            if self.sampling_config.default_rate < 0 or self.sampling_config.default_rate > 1:
                issues.append("sampling default_rate must be between 0 and 1. "
                            "Set UCBL_SAMPLING_DEFAULT_RATE environment variable.")
            
            if self.sampling_config.volume_threshold <= 0:
                issues.append("sampling volume_threshold must be positive. "
                            "Set UCBL_SAMPLING_VOLUME_THRESHOLD environment variable.")
            
            if hasattr(self.sampling_config, 'level_rates') and self.sampling_config.level_rates:
                for level, rate in self.sampling_config.level_rates.items():
                    if rate < 0 or rate > 1:
                        issues.append(f"sampling rate for {level} must be between 0 and 1. Current: {rate}")
        
        # Buffer configuration validation
        if self.buffer_config:
            if self.buffer_config.max_size <= 0:
                issues.append("buffer max_size must be positive. "
                            "Set UCBL_BUFFER_MAX_SIZE environment variable.")
            elif self.buffer_config.max_size > 1000000:
                issues.append("buffer max_size is very large (>1M). Consider reducing for memory efficiency.")
            
            if self.buffer_config.flush_interval_seconds <= 0:
                issues.append("buffer flush_interval_seconds must be positive. "
                            "Set UCBL_BUFFER_FLUSH_INTERVAL environment variable.")
            
            if hasattr(self.buffer_config, 'batch_size') and self.buffer_config.batch_size <= 0:
                issues.append("buffer batch_size must be positive")
        
        # Performance thresholds validation
        if self.performance_thresholds:
            if (self.performance_thresholds.cpu_warning_percent >= 
                self.performance_thresholds.cpu_critical_percent):
                issues.append("CPU warning threshold must be less than critical threshold. "
                            "Check UCBL_CPU_WARNING_THRESHOLD and UCBL_CPU_CRITICAL_THRESHOLD.")
            
            if (self.performance_thresholds.memory_warning_percent >= 
                self.performance_thresholds.memory_critical_percent):
                issues.append("Memory warning threshold must be less than critical threshold. "
                            "Check UCBL_MEMORY_WARNING_THRESHOLD and UCBL_MEMORY_CRITICAL_THRESHOLD.")
            
            # Check for reasonable threshold values
            for threshold_name, threshold_value in [
                ('cpu_warning_percent', self.performance_thresholds.cpu_warning_percent),
                ('cpu_critical_percent', self.performance_thresholds.cpu_critical_percent),
                ('memory_warning_percent', self.performance_thresholds.memory_warning_percent),
                ('memory_critical_percent', self.performance_thresholds.memory_critical_percent)
            ]:
                if threshold_value < 0 or threshold_value > 100:
                    issues.append(f"{threshold_name} must be between 0 and 100. Current: {threshold_value}")
        
        # CloudWatch configuration validation
        if self.enable_cloudwatch:
            if not self.cloudwatch_region:
                issues.append("CloudWatch region is required when CloudWatch is enabled. "
                            "Set AWS_REGION environment variable.")
            
            if self.cloudwatch_batch_size <= 0:
                issues.append("CloudWatch batch_size must be positive")
            elif self.cloudwatch_batch_size > 10000:
                issues.append("CloudWatch batch_size is very large. AWS CloudWatch has limits.")
        
        # Health monitoring validation
        if self.enable_health_monitoring:
            if self.health_endpoint_port < 1 or self.health_endpoint_port > 65535:
                issues.append("health_endpoint_port must be between 1 and 65535")
            
            if not self.health_endpoint_path.startswith('/'):
                issues.append("health_endpoint_path must start with '/'")
        
        # Advanced configuration validation
        if self.max_log_size_bytes <= 0:
            issues.append("max_log_size_bytes must be positive")
        elif self.max_log_size_bytes > 10 * 1024 * 1024:  # 10MB
            issues.append("max_log_size_bytes is very large (>10MB). Consider reducing for performance.")
        
        # Redaction patterns validation
        if self.enable_data_redaction and self.redaction_patterns:
            import re
            for i, pattern in enumerate(self.redaction_patterns):
                try:
                    re.compile(pattern)
                except re.error as e:
                    issues.append(f"Invalid regex pattern at index {i}: {pattern}. Error: {e}")
        
        return issues
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'EnhancedEKSConfig':
        """
        Load configuration from JSON or YAML file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            EnhancedEKSConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    try:
                        import yaml
                        config_dict = yaml.safe_load(f)
                    except ImportError:
                        raise ValueError("PyYAML is required to load YAML configuration files")
                elif file_path.suffix.lower() == '.json':
                    config_dict = json.load(f)
                else:
                    # Try JSON first, then YAML
                    content = f.read()
                    try:
                        config_dict = json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            import yaml
                            config_dict = yaml.safe_load(content)
                        except ImportError:
                            raise ValueError("Unable to parse configuration file. Install PyYAML for YAML support.")
        
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {file_path}: {e}")
        
        return cls.from_dict(config_dict)
    
    def merge_from_file(self, file_path: Union[str, Path]) -> 'EnhancedEKSConfig':
        """
        Merge configuration from file with current configuration
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            New EnhancedEKSConfig instance with merged configuration
        """
        file_config = self.from_file(file_path)
        return self.merge_with(file_config)
    
    def merge_with(self, other: 'EnhancedEKSConfig') -> 'EnhancedEKSConfig':
        """
        Merge with another configuration (other takes precedence)
        
        Args:
            other: Configuration to merge with
            
        Returns:
            New EnhancedEKSConfig instance with merged configuration
        """
        # Convert both to dict and merge
        base_dict = self.to_dict()
        other_dict = other.to_dict()
        
        # Deep merge dictionaries
        merged_dict = _deep_merge_dicts(base_dict, other_dict)
        
        return self.from_dict(merged_dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EnhancedEKSConfig':
        """
        Create configuration from dictionary with comprehensive parsing
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            EnhancedEKSConfig instance
        """
        # Extract basic configuration
        service_name = config_dict.get('service_name', 'graphrag-toolkit')
        namespace = config_dict.get('namespace', 'default')
        log_level = config_dict.get('log_level', 'INFO')
        
        # Extract feature flags
        features = config_dict.get('features', {})
        enable_tracing = features.get('tracing', True)
        enable_performance_monitoring = features.get('performance_monitoring', True)
        enable_kubernetes_metadata = features.get('kubernetes_metadata', True)
        enable_sampling = features.get('sampling', True)
        enable_security_logging = features.get('security_logging', True)
        enable_health_monitoring = features.get('health_monitoring', True)
        enable_cloudwatch = features.get('cloudwatch', True)
        
        # Create component configurations
        sampling_config = None
        if enable_sampling and 'sampling_config' in config_dict:
            sampling_dict = config_dict['sampling_config']
            sampling_config = SamplingConfig(**sampling_dict)
        
        buffer_config = None
        if 'buffer_config' in config_dict:
            buffer_dict = config_dict['buffer_config']
            buffer_config = BufferConfig(**buffer_dict)
        
        performance_thresholds = None
        if 'performance_thresholds' in config_dict:
            thresholds_dict = config_dict['performance_thresholds']
            performance_thresholds = PerformanceThresholds(**thresholds_dict)
        
        # Extract CloudWatch configuration
        cloudwatch = config_dict.get('cloudwatch', {})
        cloudwatch_log_group = cloudwatch.get('log_group')
        cloudwatch_log_stream = cloudwatch.get('log_stream')
        cloudwatch_region = cloudwatch.get('region')
        cloudwatch_batch_size = cloudwatch.get('batch_size', 100)
        cloudwatch_flush_interval = cloudwatch.get('flush_interval', 5)
        
        # Extract OpenTelemetry configuration
        otel = config_dict.get('opentelemetry', {})
        otel_endpoint = otel.get('endpoint')
        otel_service_name = otel.get('service_name')
        otel_service_version = otel.get('service_version')
        otel_headers = otel.get('headers')
        
        # Extract security configuration
        security = config_dict.get('security', {})
        enable_data_redaction = security.get('enable_data_redaction', True)
        redaction_patterns = security.get('redaction_patterns', [])
        
        # Extract health configuration
        health = config_dict.get('health', {})
        health_check_interval = health.get('check_interval', 30)
        health_endpoint_port = health.get('endpoint_port', 8080)
        health_endpoint_path = health.get('endpoint_path', '/health')
        
        # Extract advanced configuration
        advanced = config_dict.get('advanced', {})
        max_log_size_bytes = advanced.get('max_log_size_bytes', 1024 * 1024)
        enable_structured_logging = advanced.get('enable_structured_logging', True)
        timezone = advanced.get('timezone', 'UTC')
        
        # Create configuration object
        config = cls(
            service_name=service_name,
            namespace=namespace,
            log_level=log_level,
            enable_tracing=enable_tracing,
            enable_performance_monitoring=enable_performance_monitoring,
            enable_kubernetes_metadata=enable_kubernetes_metadata,
            enable_sampling=enable_sampling,
            enable_security_logging=enable_security_logging,
            enable_health_monitoring=enable_health_monitoring,
            enable_cloudwatch=enable_cloudwatch,
            sampling_config=sampling_config,
            buffer_config=buffer_config,
            performance_thresholds=performance_thresholds,
            cloudwatch_log_group=cloudwatch_log_group,
            cloudwatch_log_stream=cloudwatch_log_stream,
            cloudwatch_region=cloudwatch_region,
            cloudwatch_batch_size=cloudwatch_batch_size,
            cloudwatch_flush_interval=cloudwatch_flush_interval,
            otel_endpoint=otel_endpoint,
            otel_service_name=otel_service_name,
            otel_service_version=otel_service_version,
            otel_headers=otel_headers,
            enable_data_redaction=enable_data_redaction,
            redaction_patterns=redaction_patterns,
            health_check_interval=health_check_interval,
            health_endpoint_port=health_endpoint_port,
            health_endpoint_path=health_endpoint_path,
            max_log_size_bytes=max_log_size_bytes,
            enable_structured_logging=enable_structured_logging,
            timezone=timezone
        )
        
        return config
    
    def save_to_file(self, file_path: Union[str, Path], format: str = 'auto') -> None:
        """
        Save configuration to file
        
        Args:
            file_path: Path to save configuration
            format: File format ('json', 'yaml', or 'auto' to detect from extension)
        """
        file_path = Path(file_path)
        
        # Determine format
        if format == 'auto':
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                format = 'yaml'
            else:
                format = 'json'
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.to_dict()
        
        with open(file_path, 'w') as f:
            if format == 'yaml':
                try:
                    import yaml
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                except ImportError:
                    raise ValueError("PyYAML is required to save YAML configuration files")
            else:
                json.dump(config_dict, f, indent=2)
    
    def get_environment_variables_documentation(self) -> Dict[str, str]:
        """
        Get documentation for all supported environment variables
        
        Returns:
            Dictionary mapping environment variable names to descriptions
        """
        return {
            # Basic configuration
            'UCBL_SERVICE_NAME': 'Name of the service (default: graphrag-toolkit)',
            'KUBERNETES_NAMESPACE': 'Kubernetes namespace (default: default)',
            'UCBL_LOG_LEVEL': 'Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
            
            # Feature flags
            'UCBL_ENABLE_TRACING': 'Enable distributed tracing (true/false)',
            'UCBL_ENABLE_PERFORMANCE': 'Enable performance monitoring (true/false)',
            'UCBL_ENABLE_K8S_METADATA': 'Enable Kubernetes metadata collection (true/false)',
            'UCBL_ENABLE_SAMPLING': 'Enable log sampling (true/false)',
            'UCBL_ENABLE_SECURITY': 'Enable security logging (true/false)',
            'UCBL_ENABLE_HEALTH': 'Enable health monitoring (true/false)',
            'UCBL_ENABLE_CLOUDWATCH': 'Enable CloudWatch integration (true/false)',
            
            # Sampling configuration
            'UCBL_SAMPLING_ENABLED': 'Enable sampling engine (true/false)',
            'UCBL_SAMPLING_DEFAULT_RATE': 'Default sampling rate (0.0-1.0)',
            'UCBL_SAMPLING_VOLUME_THRESHOLD': 'Volume threshold for adaptive sampling',
            'UCBL_SAMPLING_WINDOW_SIZE': 'Sampling window size in seconds',
            'UCBL_SAMPLING_PRESERVE_ERRORS': 'Always preserve error logs (true/false)',
            'UCBL_SAMPLING_DEBUG_MODE': 'Enable sampling debug mode (true/false)',
            'UCBL_SAMPLING_RATE_DEBUG': 'Sampling rate for DEBUG logs (0.0-1.0)',
            'UCBL_SAMPLING_RATE_INFO': 'Sampling rate for INFO logs (0.0-1.0)',
            'UCBL_SAMPLING_RATE_WARNING': 'Sampling rate for WARNING logs (0.0-1.0)',
            'UCBL_SAMPLING_RATE_ERROR': 'Sampling rate for ERROR logs (0.0-1.0)',
            'UCBL_SAMPLING_RATE_CRITICAL': 'Sampling rate for CRITICAL logs (0.0-1.0)',
            
            # Buffer configuration
            'UCBL_BUFFER_MAX_SIZE': 'Maximum buffer size in entries',
            'UCBL_BUFFER_FLUSH_INTERVAL': 'Buffer flush interval in seconds',
            'UCBL_BUFFER_MAX_RETRIES': 'Maximum retry attempts for failed deliveries',
            'UCBL_BUFFER_BACKOFF_MULTIPLIER': 'Exponential backoff multiplier',
            'UCBL_BUFFER_COMPRESSION': 'Enable log compression (true/false)',
            'UCBL_BUFFER_BATCH_SIZE': 'Batch size for log delivery',
            
            # Performance thresholds
            'UCBL_CPU_WARNING_THRESHOLD': 'CPU usage warning threshold (0-100)',
            'UCBL_CPU_CRITICAL_THRESHOLD': 'CPU usage critical threshold (0-100)',
            'UCBL_MEMORY_WARNING_THRESHOLD': 'Memory usage warning threshold (0-100)',
            'UCBL_MEMORY_CRITICAL_THRESHOLD': 'Memory usage critical threshold (0-100)',
            
            # CloudWatch configuration
            'UCBL_CLOUDWATCH_LOG_GROUP': 'CloudWatch log group name',
            'UCBL_CLOUDWATCH_LOG_STREAM': 'CloudWatch log stream name',
            'AWS_REGION': 'AWS region for CloudWatch',
            'UCBL_CLOUDWATCH_BATCH_SIZE': 'CloudWatch batch size',
            'UCBL_CLOUDWATCH_FLUSH_INTERVAL': 'CloudWatch flush interval in seconds',
            
            # OpenTelemetry configuration
            'OTEL_EXPORTER_OTLP_ENDPOINT': 'OpenTelemetry OTLP endpoint',
            'OTEL_SERVICE_NAME': 'OpenTelemetry service name',
            'OTEL_SERVICE_VERSION': 'OpenTelemetry service version',
            'OTEL_EXPORTER_OTLP_HEADERS': 'OpenTelemetry headers (key1=value1,key2=value2)',
            
            # Security configuration
            'UCBL_ENABLE_DATA_REDACTION': 'Enable sensitive data redaction (true/false)',
            'UCBL_REDACTION_PATTERNS': 'Custom redaction patterns (JSON array or comma-separated)',
            
            # Health monitoring
            'UCBL_HEALTH_CHECK_INTERVAL': 'Health check interval in seconds',
            'UCBL_HEALTH_PORT': 'Health endpoint port',
            'UCBL_HEALTH_PATH': 'Health endpoint path',
            
            # Advanced configuration
            'UCBL_MAX_LOG_SIZE_BYTES': 'Maximum log entry size in bytes',
            'UCBL_STRUCTURED_LOGGING': 'Enable structured logging (true/false)',
            'UCBL_TIMEZONE': 'Timezone for log timestamps',
            'UCBL_CONFIG_FILE': 'Path to configuration file',
            'UCBL_SECRETS_FILE': 'Path to secrets file'
        }


def _get_bool_env(key: str, default: bool) -> bool:
    """Get boolean value from environment variable"""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def _get_int_env(key: str, default: int) -> int:
    """Get integer value from environment variable"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float_env(key: str, default: float) -> float:
    """Get float value from environment variable"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


class ConfigurationManager:
    """
    Advanced configuration manager with validation, environment detection,
    and deployment-specific optimizations.
    """
    
    @staticmethod
    def create_for_environment(environment: str = 'auto') -> EnhancedEKSConfig:
        """
        Create configuration optimized for specific environment
        
        Args:
            environment: Target environment ('development', 'staging', 'production', 'auto')
            
        Returns:
            EnhancedEKSConfig optimized for the environment
        """
        if environment == 'auto':
            environment = ConfigurationManager.detect_environment()
        
        if environment == 'development':
            return ConfigurationManager._create_development_config()
        elif environment == 'staging':
            return ConfigurationManager._create_staging_config()
        elif environment == 'production':
            return ConfigurationManager._create_production_config()
        else:
            # Default to production-like configuration
            return ConfigurationManager._create_production_config()
    
    @staticmethod
    def detect_environment() -> str:
        """
        Detect current environment based on environment variables and context
        
        Returns:
            Detected environment ('development', 'staging', 'production')
        """
        # Check explicit environment variable
        env = os.getenv('ENVIRONMENT', os.getenv('ENV', '')).lower()
        if env in ['dev', 'development']:
            return 'development'
        elif env in ['stage', 'staging']:
            return 'staging'
        elif env in ['prod', 'production']:
            return 'production'
        
        # Check Kubernetes namespace patterns
        namespace = os.getenv('KUBERNETES_NAMESPACE', '')
        if 'dev' in namespace or 'development' in namespace:
            return 'development'
        elif 'stage' in namespace or 'staging' in namespace:
            return 'staging'
        elif 'prod' in namespace or 'production' in namespace:
            return 'production'
        
        # Check for development indicators
        if os.getenv('DEBUG') or os.getenv('DEVELOPMENT'):
            return 'development'
        
        # Default to production for safety
        return 'production'
    
    @staticmethod
    def _create_development_config() -> EnhancedEKSConfig:
        """Create development-optimized configuration"""
        config = EnhancedEKSConfig.from_environment()
        
        # Development-friendly settings
        config.log_level = 'DEBUG'
        config.enable_sampling = False  # No sampling in development
        config.enable_cloudwatch = False  # Usually not needed in dev
        
        # Smaller buffers for faster feedback
        if config.buffer_config:
            config.buffer_config.max_size = 1000
            config.buffer_config.flush_interval_seconds = 1
            config.buffer_config.batch_size = 10
        
        # Relaxed performance thresholds
        if config.performance_thresholds:
            config.performance_thresholds.cpu_warning_percent = 90.0
            config.performance_thresholds.cpu_critical_percent = 98.0
            config.performance_thresholds.memory_warning_percent = 90.0
            config.performance_thresholds.memory_critical_percent = 98.0
        
        return config
    
    @staticmethod
    def _create_staging_config() -> EnhancedEKSConfig:
        """Create staging-optimized configuration"""
        config = EnhancedEKSConfig.from_environment()
        
        # Staging settings (production-like but with more logging)
        config.log_level = 'INFO'
        config.enable_sampling = True
        
        # Moderate sampling for staging
        if config.sampling_config:
            config.sampling_config.default_rate = 0.5  # 50% sampling
            config.sampling_config.level_rates = {
                'DEBUG': 0.1,
                'INFO': 0.3,
                'WARNING': 0.8,
                'ERROR': 1.0,
                'CRITICAL': 1.0
            }
        
        return config
    
    @staticmethod
    def _create_production_config() -> EnhancedEKSConfig:
        """Create production-optimized configuration"""
        config = EnhancedEKSConfig.from_environment()
        
        # Production settings
        config.log_level = 'INFO'
        config.enable_sampling = True
        
        # Aggressive sampling for production
        if config.sampling_config:
            config.sampling_config.default_rate = 0.1  # 10% sampling
            config.sampling_config.level_rates = {
                'DEBUG': 0.01,   # 1% of debug logs
                'INFO': 0.05,    # 5% of info logs
                'WARNING': 0.5,  # 50% of warning logs
                'ERROR': 1.0,    # All error logs
                'CRITICAL': 1.0  # All critical logs
            }
            config.sampling_config.volume_threshold = 5000
        
        # Larger buffers for production efficiency
        if config.buffer_config:
            config.buffer_config.max_size = 50000
            config.buffer_config.flush_interval_seconds = 10
            config.buffer_config.batch_size = 500
        
        # Strict performance thresholds
        if config.performance_thresholds:
            config.performance_thresholds.cpu_warning_percent = 70.0
            config.performance_thresholds.cpu_critical_percent = 85.0
            config.performance_thresholds.memory_warning_percent = 75.0
            config.performance_thresholds.memory_critical_percent = 90.0
        
        return config
    
    @staticmethod
    def validate_and_suggest_fixes(config: EnhancedEKSConfig) -> Dict[str, Any]:
        """
        Validate configuration and provide suggestions for fixes
        
        Args:
            config: Configuration to validate
            
        Returns:
            Dictionary with validation results and suggestions
        """
        issues = config.validate()
        
        suggestions = []
        warnings = []
        
        # Analyze configuration and provide suggestions
        if config.enable_sampling and config.sampling_config:
            if config.sampling_config.default_rate > 0.5:
                warnings.append("High default sampling rate may impact performance in high-volume scenarios")
        
        if config.buffer_config and config.buffer_config.max_size > 100000:
            warnings.append("Large buffer size may consume significant memory")
        
        if config.enable_cloudwatch and not config.cloudwatch_region:
            suggestions.append("Set AWS_REGION environment variable for CloudWatch integration")
        
        if not config.enable_health_monitoring:
            suggestions.append("Consider enabling health monitoring for better observability")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'suggestions': suggestions,
            'environment_variables': config.get_environment_variables_documentation()
        }