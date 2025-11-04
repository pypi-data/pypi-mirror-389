"""
Factory for creating enhanced EKS loggers

This module provides factory methods for creating enhanced EKS loggers
with different configurations and component combinations.
"""

from typing import Optional, Dict, Any
from .config import EnhancedEKSConfig
from .enhanced_eks_logger import EnhancedEKSLoggerBase
from .enhanced_eks_logger_impl import EnhancedEKSLogger
from .sampling.models import SamplingConfig
from .buffering.models import BufferConfig
from .performance.models import PerformanceThresholds


class EnhancedEKSLoggerFactory:
    """Factory for creating enhanced EKS loggers"""
    
    @staticmethod
    def create_logger(config: Optional[EnhancedEKSConfig] = None,
                     service_name: Optional[str] = None,
                     namespace: Optional[str] = None,
                     **kwargs) -> EnhancedEKSLoggerBase:
        """
        Create an enhanced EKS logger instance
        
        Args:
            config: Complete configuration object (optional)
            service_name: Service name override (optional)
            namespace: Namespace override (optional)
            **kwargs: Additional configuration parameters
            
        Returns:
            EnhancedEKSLoggerBase instance (note: this is the base class,
            concrete implementation will be provided in later tasks)
        """
        # Use provided config or create from environment
        if config is None:
            config = EnhancedEKSConfig.from_environment()
        
        # Override with explicit parameters
        if service_name:
            config.service_name = service_name
        if namespace:
            config.namespace = namespace
        
        # Apply additional kwargs to config
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Validate configuration
        issues = config.validate()
        if issues:
            raise ValueError(f"Configuration validation failed: {', '.join(issues)}")
        
        # Create logger instance with concrete implementation
        return EnhancedEKSLogger(
            service_name=config.service_name,
            namespace=config.namespace,
            enable_tracing=config.enable_tracing,
            enable_performance_monitoring=config.enable_performance_monitoring,
            enable_kubernetes_metadata=config.enable_kubernetes_metadata,
            enable_sampling=config.enable_sampling,
            enable_security_logging=config.enable_security_logging,
            sampling_config=config.sampling_config,
            buffer_config=config.buffer_config,
            performance_thresholds=config.performance_thresholds
        )
    
    @staticmethod
    def create_minimal_logger(service_name: str, namespace: str = "default") -> EnhancedEKSLoggerBase:
        """
        Create a minimal enhanced logger with basic features only
        
        Args:
            service_name: Name of the service
            namespace: Kubernetes namespace
            
        Returns:
            EnhancedEKSLoggerBase with minimal features enabled
        """
        config = EnhancedEKSConfig(
            service_name=service_name,
            namespace=namespace,
            enable_tracing=False,
            enable_performance_monitoring=False,
            enable_kubernetes_metadata=True,  # Keep basic K8s metadata
            enable_sampling=False,
            enable_security_logging=False,
            enable_health_monitoring=True  # Keep health monitoring for basic observability
        )
        
        return EnhancedEKSLoggerFactory.create_logger(config)
    
    @staticmethod
    def create_development_logger(service_name: str, namespace: str = "default") -> EnhancedEKSLoggerBase:
        """
        Create a logger optimized for development environments
        
        Args:
            service_name: Name of the service
            namespace: Kubernetes namespace
            
        Returns:
            EnhancedEKSLoggerBase optimized for development
        """
        # Development-friendly sampling config
        sampling_config = SamplingConfig(
            enabled=False,  # Disable sampling in development
            debug_mode=True
        )
        
        # Smaller buffer for faster feedback
        buffer_config = BufferConfig(
            max_size=1000,
            flush_interval_seconds=1,
            batch_size=10
        )
        
        # Relaxed performance thresholds
        performance_thresholds = PerformanceThresholds(
            cpu_warning_percent=90.0,
            cpu_critical_percent=98.0,
            memory_warning_percent=90.0,
            memory_critical_percent=98.0
        )
        
        config = EnhancedEKSConfig(
            service_name=service_name,
            namespace=namespace,
            enable_tracing=True,
            enable_performance_monitoring=True,
            enable_kubernetes_metadata=True,
            enable_sampling=False,  # No sampling in development
            enable_security_logging=True,
            enable_health_monitoring=True,
            sampling_config=sampling_config,
            buffer_config=buffer_config,
            performance_thresholds=performance_thresholds
        )
        
        return EnhancedEKSLoggerFactory.create_logger(config)
    
    @staticmethod
    def create_production_logger(service_name: str, namespace: str = "default") -> EnhancedEKSLoggerBase:
        """
        Create a logger optimized for production environments
        
        Args:
            service_name: Name of the service
            namespace: Kubernetes namespace
            
        Returns:
            EnhancedEKSLoggerBase optimized for production
        """
        # Production-optimized sampling config
        sampling_config = SamplingConfig(
            enabled=True,
            strategy="adaptive",
            default_rate=0.1,  # Sample 10% by default
            level_rates={
                'DEBUG': 0.01,    # 1% of debug logs
                'INFO': 0.05,     # 5% of info logs
                'WARNING': 0.5,   # 50% of warning logs
                'ERROR': 1.0,     # All error logs
                'CRITICAL': 1.0   # All critical logs
            },
            volume_threshold=5000,  # Higher threshold for production
            preserve_errors=True
        )
        
        # Larger buffer for production efficiency
        buffer_config = BufferConfig(
            max_size=50000,
            flush_interval_seconds=10,
            batch_size=500,
            enable_compression=True
        )
        
        # Strict performance thresholds for production
        performance_thresholds = PerformanceThresholds(
            cpu_warning_percent=70.0,
            cpu_critical_percent=85.0,
            memory_warning_percent=75.0,
            memory_critical_percent=90.0
        )
        
        config = EnhancedEKSConfig(
            service_name=service_name,
            namespace=namespace,
            enable_tracing=True,
            enable_performance_monitoring=True,
            enable_kubernetes_metadata=True,
            enable_sampling=True,
            enable_security_logging=True,
            enable_health_monitoring=True,
            sampling_config=sampling_config,
            buffer_config=buffer_config,
            performance_thresholds=performance_thresholds
        )
        
        return EnhancedEKSLoggerFactory.create_logger(config)
    
    @staticmethod
    def create_from_dict(config_dict: Dict[str, Any]) -> EnhancedEKSLoggerBase:
        """
        Create logger from dictionary configuration
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            EnhancedEKSLoggerBase instance
        """
        # Extract basic configuration
        service_name = config_dict.get('service_name', 'graphrag-toolkit')
        namespace = config_dict.get('namespace', 'default')
        
        # Extract feature flags
        features = config_dict.get('features', {})
        enable_tracing = features.get('tracing', True)
        enable_performance_monitoring = features.get('performance_monitoring', True)
        enable_kubernetes_metadata = features.get('kubernetes_metadata', True)
        enable_sampling = features.get('sampling', True)
        enable_security_logging = features.get('security_logging', True)
        enable_health_monitoring = features.get('health_monitoring', True)
        
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
        
        # Create configuration object
        config = EnhancedEKSConfig(
            service_name=service_name,
            namespace=namespace,
            enable_tracing=enable_tracing,
            enable_performance_monitoring=enable_performance_monitoring,
            enable_kubernetes_metadata=enable_kubernetes_metadata,
            enable_sampling=enable_sampling,
            enable_security_logging=enable_security_logging,
            enable_health_monitoring=enable_health_monitoring,
            sampling_config=sampling_config,
            buffer_config=buffer_config,
            performance_thresholds=performance_thresholds
        )
        
        return EnhancedEKSLoggerFactory.create_logger(config)