"""
Enhanced EKS Logger Components

This package contains enhanced logging components optimized for EKS container deployments,
including distributed tracing, Kubernetes metadata collection, performance monitoring,
and intelligent log sampling.
"""

from .interfaces import IEnhancedEKSLogger
from .tracing import ITracingManager, BaseTracingManager
from .metadata import IMetadataCollector, BaseMetadataCollector
from .performance import IPerformanceMonitor, BasePerformanceMonitor
from .sampling import ISamplingEngine, BaseSamplingEngine
from .buffering import IBufferManager, BaseBufferManager
from .health import IHealthMonitor, BaseHealthMonitor
from .security import ISecurityContextLogger, BaseSecurityContextLogger
from .cloudwatch import ICloudWatchHandler, EnhancedCloudWatchHandler

from .models import EnhancedLogEntry
from .tracing.models import TraceContext
from .sampling.models import SamplingConfig, SamplingDecision, SamplingStrategy
from .buffering.models import BufferConfig
from .performance.models import PerformanceThresholds, SystemMetrics
from .health.models import HealthStatus, HealthState
from .metadata.models import KubernetesMetadata
from .security.models import SecurityContext
from .cloudwatch.models import CloudWatchConfig, LogBatch, CloudWatchDestination

from .enhanced_eks_logger import EnhancedEKSLoggerBase
from .enhanced_eks_logger_impl import EnhancedEKSLogger
from .config import EnhancedEKSConfig, ConfigurationManager
from .factory import EnhancedEKSLoggerFactory
from .initialization import LoggerInitializer, initialize_enhanced_logger, quick_setup, InitializationError

__all__ = [
    # Interfaces
    'ITracingManager',
    'IMetadataCollector', 
    'IPerformanceMonitor',
    'ISamplingEngine',
    'IBufferManager',
    'IHealthMonitor',
    'ISecurityContextLogger',
    'IEnhancedEKSLogger',
    'ICloudWatchHandler',
    # Base implementations
    'BaseTracingManager',
    'BaseMetadataCollector',
    'BasePerformanceMonitor',
    'BaseSamplingEngine',
    'BaseBufferManager',
    'BaseHealthMonitor',
    'BaseSecurityContextLogger',
    # CloudWatch
    'EnhancedCloudWatchHandler',
    # Models
    'EnhancedLogEntry',
    'TraceContext',
    'SamplingConfig',
    'BufferConfig',
    'PerformanceThresholds',
    'HealthStatus',
    'SystemMetrics',
    'KubernetesMetadata',
    'SecurityContext',
    'SamplingDecision',
    'SamplingStrategy',
    'HealthState',
    'CloudWatchConfig',
    'LogBatch',
    'CloudWatchDestination',
    # Main classes
    'EnhancedEKSLoggerBase',
    'EnhancedEKSLogger',
    'EnhancedEKSConfig',
    'EnhancedEKSLoggerFactory',
    # Configuration and initialization
    'ConfigurationManager',
    'LoggerInitializer',
    'initialize_enhanced_logger',
    'quick_setup',
    'InitializationError'
]