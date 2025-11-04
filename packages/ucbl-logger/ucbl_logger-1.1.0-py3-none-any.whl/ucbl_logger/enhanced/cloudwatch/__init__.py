"""
CloudWatch Integration Components

This package contains CloudWatch integration components for optimized log delivery
to AWS CloudWatch Logs with intelligent batching, rate limiting, and cost optimization.
"""

from .interfaces import ICloudWatchHandler, IBatcher, IRateLimiter, ICompressor, IMultiDestinationHandler
from .models import (
    CloudWatchConfig, BatchConfig, CompressionConfig, LogBatch, LogEntry,
    CloudWatchDestination, DeliveryStats, RateLimitState, CompressionType, BackoffStrategy
)
from .handler import EnhancedCloudWatchHandler, MultiDestinationCloudWatchHandler
from .batching import IntelligentBatcher, PriorityBatcher
from .rate_limiter import CloudWatchRateLimiter, AdaptiveRateLimiter
from .compression import LogCompressor, LogDeduplicator, SmartDeduplicator
from .auto_config import CloudWatchAutoConfigurator
from .multi_destination import MultiDestinationManager, DeliveryMode
from .error_handling import CloudWatchErrorHandler, CostOptimizer, ErrorType

__all__ = [
    # Interfaces
    'ICloudWatchHandler',
    'IBatcher',
    'IRateLimiter', 
    'ICompressor',
    'IMultiDestinationHandler',
    
    # Models
    'CloudWatchConfig',
    'BatchConfig', 
    'CompressionConfig',
    'LogBatch',
    'LogEntry',
    'CloudWatchDestination',
    'DeliveryStats',
    'RateLimitState',
    'CompressionType',
    'BackoffStrategy',
    
    # Main handlers
    'EnhancedCloudWatchHandler',
    'MultiDestinationCloudWatchHandler',
    
    # Batching
    'IntelligentBatcher',
    'PriorityBatcher',
    
    # Rate limiting
    'CloudWatchRateLimiter',
    'AdaptiveRateLimiter',
    
    # Compression and deduplication
    'LogCompressor',
    'LogDeduplicator',
    'SmartDeduplicator',
    
    # Auto-configuration
    'CloudWatchAutoConfigurator',
    
    # Multi-destination
    'MultiDestinationManager',
    'DeliveryMode',
    
    # Error handling and optimization
    'CloudWatchErrorHandler',
    'CostOptimizer',
    'ErrorType'
]