"""
Enhanced interfaces for EKS-optimized logging components

These interfaces define the contracts for distributed tracing, metadata collection,
performance monitoring, and other enhanced logging capabilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .health.models import HealthStatus

# Import component-specific interfaces
from .tracing.interfaces import ITracingManager
from .metadata.interfaces import IMetadataCollector
from .performance.interfaces import IPerformanceMonitor
from .sampling.interfaces import ISamplingEngine
from .buffering.interfaces import IBufferManager
from .health.interfaces import IHealthMonitor
from .security.interfaces import ISecurityContextLogger


class IEnhancedEKSLogger(ABC):
    """Main interface for enhanced EKS logger with all capabilities"""
    
    @abstractmethod
    def info(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log info message with enhanced context"""
        pass
    
    @abstractmethod
    def debug(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log debug message with enhanced context"""
        pass
    
    @abstractmethod
    def warning(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log warning message with enhanced context"""
        pass
    
    @abstractmethod
    def error(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log error message with enhanced context"""
        pass
    
    @abstractmethod
    def critical(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log critical message with enhanced context"""
        pass
    
    @abstractmethod
    def start_trace(self, operation_name: str) -> str:
        """Start a new trace and return correlation ID"""
        pass
    
    @abstractmethod
    def end_trace(self, correlation_id: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """End a trace with optional metadata"""
        pass
    
    @abstractmethod
    def log_performance_metrics(self) -> None:
        """Log current performance metrics"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> HealthStatus:
        """Get logging system health status"""
        pass
    
    @abstractmethod
    def configure_sampling(self, config: Dict[str, Any]) -> None:
        """Configure log sampling parameters"""
        pass