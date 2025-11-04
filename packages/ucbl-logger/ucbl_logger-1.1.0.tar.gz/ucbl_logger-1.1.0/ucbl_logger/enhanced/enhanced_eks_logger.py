"""
Enhanced EKS Logger - Main interface integrating all enhanced components

This module provides the main enhanced EKS logger that orchestrates all the enhanced
components while maintaining backward compatibility with the existing UCBLLogger API.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .interfaces import IEnhancedEKSLogger
from .health.models import HealthStatus
from .sampling.models import SamplingConfig
from .buffering.models import BufferConfig
from .performance.models import PerformanceThresholds


class EnhancedEKSLoggerBase(IEnhancedEKSLogger):
    """
    Base class for Enhanced EKS Logger that provides the complete interface
    
    This class serves as the foundation for the enhanced EKS logger implementation,
    combining all enhanced capabilities with backward compatibility.
    """
    
    def __init__(self, 
                 service_name: str,
                 namespace: str = "default",
                 enable_tracing: bool = True,
                 enable_performance_monitoring: bool = True,
                 enable_kubernetes_metadata: bool = True,
                 enable_sampling: bool = True,
                 enable_security_logging: bool = True,
                 sampling_config: Optional[SamplingConfig] = None,
                 buffer_config: Optional[BufferConfig] = None,
                 performance_thresholds: Optional[PerformanceThresholds] = None):
        """
        Initialize Enhanced EKS Logger
        
        Args:
            service_name: Name of the service for logging context
            namespace: Kubernetes namespace (default: "default")
            enable_tracing: Enable distributed tracing capabilities
            enable_performance_monitoring: Enable performance metrics collection
            enable_kubernetes_metadata: Enable Kubernetes metadata collection
            enable_sampling: Enable intelligent log sampling
            enable_security_logging: Enable security context logging
            sampling_config: Configuration for log sampling
            buffer_config: Configuration for log buffering
            performance_thresholds: Performance monitoring thresholds
        """
        self.service_name = service_name
        self.namespace = namespace
        self.enable_tracing = enable_tracing
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_kubernetes_metadata = enable_kubernetes_metadata
        self.enable_sampling = enable_sampling
        self.enable_security_logging = enable_security_logging
        
        # Configuration objects
        self.sampling_config = sampling_config or SamplingConfig()
        self.buffer_config = buffer_config or BufferConfig()
        self.performance_thresholds = performance_thresholds or PerformanceThresholds()
        
        # Component instances will be initialized by concrete implementation
        self._tracing_manager = None
        self._metadata_collector = None
        self._performance_monitor = None
        self._sampling_engine = None
        self._buffer_manager = None
        self._health_monitor = None
        self._security_logger = None
    
    # Enhanced logging methods (abstract - to be implemented by concrete class)
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
    
    # Tracing methods (abstract - to be implemented by concrete class)
    @abstractmethod
    def start_trace(self, operation_name: str) -> str:
        """Start a new trace and return correlation ID"""
        pass
    
    @abstractmethod
    def end_trace(self, correlation_id: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """End a trace with optional metadata"""
        pass
    
    # Performance monitoring methods (abstract - to be implemented by concrete class)
    @abstractmethod
    def log_performance_metrics(self) -> None:
        """Log current performance metrics"""
        pass
    
    # Health monitoring methods (abstract - to be implemented by concrete class)
    @abstractmethod
    def get_health_status(self) -> HealthStatus:
        """Get logging system health status"""
        pass
    
    # Configuration methods (abstract - to be implemented by concrete class)
    @abstractmethod
    def configure_sampling(self, config: Dict[str, Any]) -> None:
        """Configure log sampling parameters"""
        pass
    
    # Backward compatibility methods from base interfaces
    def log(self, level, message: str) -> None:
        """Basic log method for backward compatibility"""
        # Map to enhanced logging methods
        level_str = level.value if hasattr(level, 'value') else str(level)
        if level_str == "INFO":
            self.info(message)
        elif level_str == "DEBUG":
            self.debug(message)
        elif level_str == "ERROR":
            self.error(message)
        elif level_str == "CRITICAL":
            self.critical(message)
        else:
            self.info(message)  # Default to info
    
    def log_task_start(self, task_name: str, task_type: str = "System") -> None:
        """Task start logging for backward compatibility"""
        correlation_id = self.start_trace(f"task_{task_name}") if self.enable_tracing else None
        self.info(f"Task started: {task_name}", 
                 correlation_id=correlation_id,
                 task_name=task_name, 
                 task_type=task_type, 
                 event_type="task_start")
    
    def log_task_stop(self, task_name: str) -> None:
        """Task stop logging for backward compatibility"""
        self.info(f"Task completed: {task_name}", 
                 task_name=task_name, 
                 event_type="task_stop")
    
    def log_risk(self, message: str, critical: bool = False, minor: bool = False) -> None:
        """Risk logging for backward compatibility"""
        severity = "critical" if critical else "minor" if minor else "medium"
        level_method = self.critical if critical else self.error
        level_method(f"Risk detected: {message}", 
                    event_type="risk", 
                    risk_severity=severity)
    
    def log_anomaly(self, message: str) -> None:
        """Anomaly logging for backward compatibility"""
        self.error(f"Anomaly detected: {message}", 
                  event_type="anomaly")
    
    # Enhanced versions of backward compatibility methods
    def log_task_start_enhanced(self, task_name: str, task_type: str = "System", 
                              correlation_id: Optional[str] = None, **kwargs) -> Optional[str]:
        """Enhanced task start with explicit correlation ID support"""
        if correlation_id is None and self.enable_tracing:
            correlation_id = self.start_trace(f"task_{task_name}")
        
        self.info(f"Task started: {task_name}", 
                 correlation_id=correlation_id,
                 task_name=task_name, 
                 task_type=task_type, 
                 event_type="task_start",
                 **kwargs)
        return correlation_id
    
    def log_task_stop_enhanced(self, task_name: str, correlation_id: Optional[str] = None, 
                             success: bool = True, **kwargs) -> None:
        """Enhanced task stop with explicit correlation ID support"""
        self.info(f"Task completed: {task_name}", 
                 correlation_id=correlation_id,
                 task_name=task_name, 
                 event_type="task_stop",
                 success=success,
                 **kwargs)
        
        if correlation_id and self.enable_tracing:
            self.end_trace(correlation_id, success)
    
    def log_risk_enhanced(self, message: str, critical: bool = False, minor: bool = False,
                         correlation_id: Optional[str] = None, 
                         security_context: Optional[Dict[str, Any]] = None,
                         **kwargs) -> None:
        """Enhanced risk logging with security context"""
        severity = "critical" if critical else "minor" if minor else "medium"
        level_method = self.critical if critical else self.error
        
        log_kwargs = {
            'correlation_id': correlation_id,
            'event_type': 'risk',
            'risk_severity': severity,
            **kwargs
        }
        
        if security_context:
            log_kwargs['security_context'] = security_context
            
        level_method(f"Risk detected: {message}", **log_kwargs)
    
    def log_anomaly_enhanced(self, message: str, correlation_id: Optional[str] = None,
                           performance_context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Enhanced anomaly logging with performance context"""
        log_kwargs = {
            'correlation_id': correlation_id,
            'event_type': 'anomaly',
            **kwargs
        }
        
        if performance_context:
            log_kwargs['performance_context'] = performance_context
            
        self.error(f"Anomaly detected: {message}", **log_kwargs)
    
    # Utility methods for feature management
    def is_tracing_enabled(self) -> bool:
        """Check if tracing is enabled"""
        return self.enable_tracing
    
    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled"""
        return self.enable_performance_monitoring
    
    def is_sampling_enabled(self) -> bool:
        """Check if sampling is enabled"""
        return self.enable_sampling
    
    def is_security_logging_enabled(self) -> bool:
        """Check if security logging is enabled"""
        return self.enable_security_logging
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            'service_name': self.service_name,
            'namespace': self.namespace,
            'features': {
                'tracing': self.enable_tracing,
                'performance_monitoring': self.enable_performance_monitoring,
                'kubernetes_metadata': self.enable_kubernetes_metadata,
                'sampling': self.enable_sampling,
                'security_logging': self.enable_security_logging
            },
            'sampling_config': self.sampling_config.__dict__ if self.sampling_config else None,
            'buffer_config': self.buffer_config.__dict__ if self.buffer_config else None,
            'performance_thresholds': self.performance_thresholds.__dict__ if self.performance_thresholds else None
        }