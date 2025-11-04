"""
Complete Enhanced EKS Logger Implementation

This module provides the complete implementation of the Enhanced EKS Logger
that orchestrates all enhanced components while maintaining backward compatibility.
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from .enhanced_eks_logger import EnhancedEKSLoggerBase
from .config import EnhancedEKSConfig
from .models import EnhancedLogEntry
from .health.models import HealthStatus, HealthState

# Import all component implementations
from .tracing.base import BaseTracingManager
from .metadata.kubernetes_collector import KubernetesMetadataCollector
from .performance.monitor import EnhancedPerformanceMonitor
from .sampling.advanced_engine import AdvancedSamplingEngine
from .buffering.enhanced_manager import EnhancedBufferManager
from .health.base import BaseHealthMonitor
from .security.base import BaseSecurityContextLogger
from .cloudwatch.handler import EnhancedCloudWatchHandler

# Import interfaces for type checking
from .interfaces import IEnhancedEKSLogger
from .tracing.interfaces import ITracingManager
from .metadata.interfaces import IMetadataCollector
from .performance.interfaces import IPerformanceMonitor
from .sampling.interfaces import ISamplingEngine
from .buffering.interfaces import IBufferManager
from .health.interfaces import IHealthMonitor
from .security.interfaces import ISecurityContextLogger
from .cloudwatch.interfaces import ICloudWatchHandler


class EnhancedEKSLogger(EnhancedEKSLoggerBase):
    """
    Complete Enhanced EKS Logger implementation
    
    This class orchestrates all enhanced components to provide comprehensive
    logging capabilities optimized for EKS container deployments.
    """
    
    def __init__(self, 
                 service_name: str,
                 namespace: str = "default",
                 enable_tracing: bool = True,
                 enable_performance_monitoring: bool = True,
                 enable_kubernetes_metadata: bool = True,
                 enable_sampling: bool = True,
                 enable_security_logging: bool = True,
                 enable_health_monitoring: bool = True,
                 enable_cloudwatch: bool = True,
                 sampling_config: Optional[Any] = None,
                 buffer_config: Optional[Any] = None,
                 performance_thresholds: Optional[Any] = None,
                 cloudwatch_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Enhanced EKS Logger with all components
        
        Args:
            service_name: Name of the service for logging context
            namespace: Kubernetes namespace
            enable_tracing: Enable distributed tracing capabilities
            enable_performance_monitoring: Enable performance metrics collection
            enable_kubernetes_metadata: Enable Kubernetes metadata collection
            enable_sampling: Enable intelligent log sampling
            enable_security_logging: Enable security context logging
            enable_health_monitoring: Enable health monitoring
            enable_cloudwatch: Enable CloudWatch integration
            sampling_config: Configuration for log sampling
            buffer_config: Configuration for log buffering
            performance_thresholds: Performance monitoring thresholds
            cloudwatch_config: CloudWatch configuration
        """
        # Initialize base class
        super().__init__(
            service_name=service_name,
            namespace=namespace,
            enable_tracing=enable_tracing,
            enable_performance_monitoring=enable_performance_monitoring,
            enable_kubernetes_metadata=enable_kubernetes_metadata,
            enable_sampling=enable_sampling,
            enable_security_logging=enable_security_logging,
            sampling_config=sampling_config,
            buffer_config=buffer_config,
            performance_thresholds=performance_thresholds
        )
        
        self.enable_health_monitoring = enable_health_monitoring
        self.enable_cloudwatch = enable_cloudwatch
        
        # Thread safety
        self._lock = threading.RLock()
        self._initialized = False
        
        # Component instances
        self._tracing_manager: Optional[ITracingManager] = None
        self._metadata_collector: Optional[IMetadataCollector] = None
        self._performance_monitor: Optional[IPerformanceMonitor] = None
        self._sampling_engine: Optional[ISamplingEngine] = None
        self._buffer_manager: Optional[IBufferManager] = None
        self._health_monitor: Optional[IHealthMonitor] = None
        self._security_logger: Optional[ISecurityContextLogger] = None
        self._cloudwatch_handler: Optional[ICloudWatchHandler] = None
        
        # Standard Python logger for fallback
        self._python_logger = logging.getLogger(f"ucbl.{service_name}")
        self._python_logger.setLevel(logging.INFO)
        
        # CloudWatch configuration
        self.cloudwatch_config = cloudwatch_config or {}
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all enhanced components"""
        with self._lock:
            if self._initialized:
                return
            
            try:
                # Initialize tracing manager
                if self.enable_tracing:
                    self._tracing_manager = BaseTracingManager(
                        service_name=self.service_name
                    )
                
                # Initialize metadata collector
                if self.enable_kubernetes_metadata:
                    self._metadata_collector = KubernetesMetadataCollector()
                
                # Initialize performance monitor
                if self.enable_performance_monitoring:
                    self._performance_monitor = EnhancedPerformanceMonitor(
                        thresholds=self.performance_thresholds,
                        collection_interval=60
                    )
                
                # Initialize sampling engine
                if self.enable_sampling:
                    self._sampling_engine = AdvancedSamplingEngine(
                        config=self.sampling_config
                    )
                
                # Initialize security logger
                if self.enable_security_logging:
                    self._security_logger = BaseSecurityContextLogger()
                
                # Initialize CloudWatch handler
                if self.enable_cloudwatch and self.cloudwatch_config:
                    self._cloudwatch_handler = EnhancedCloudWatchHandler(
                        config=self.cloudwatch_config
                    )
                
                # Initialize buffer manager (always needed for reliability)
                # Create delivery function that uses CloudWatch handler if available
                delivery_func = None
                if self._cloudwatch_handler:
                    delivery_func = lambda log_entry: self._cloudwatch_handler.send_log(log_entry)
                
                self._buffer_manager = EnhancedBufferManager(
                    config=self.buffer_config,
                    delivery_func=delivery_func
                )
                
                # Initialize health monitor
                if self.enable_health_monitoring:
                    self._health_monitor = BaseHealthMonitor()
                    
                    # Register health checks for components
                    if self._buffer_manager:
                        self._health_monitor.register_health_check(
                            'buffer_manager', 
                            lambda: getattr(self._buffer_manager, 'is_healthy', lambda: True)()
                        )
                    if self._performance_monitor:
                        self._health_monitor.register_health_check(
                            'performance_monitor', 
                            lambda: getattr(self._performance_monitor, 'is_healthy', lambda: True)()
                        )
                    if self._sampling_engine:
                        self._health_monitor.register_health_check(
                            'sampling_engine', 
                            lambda: getattr(self._sampling_engine, 'is_healthy', lambda: True)()
                        )
                
                self._initialized = True
                
                # Log successful initialization
                self._log_initialization_success()
                
            except Exception as e:
                self._python_logger.error(f"Failed to initialize enhanced components: {e}")
                # Continue with degraded functionality
                self._initialized = True
    
    def _log_initialization_success(self) -> None:
        """Log successful initialization with component status"""
        components_status = {
            'tracing': self._tracing_manager is not None,
            'metadata': self._metadata_collector is not None,
            'performance': self._performance_monitor is not None,
            'sampling': self._sampling_engine is not None,
            'security': self._security_logger is not None,
            'health': self._health_monitor is not None,
            'cloudwatch': self._cloudwatch_handler is not None,
            'buffer': self._buffer_manager is not None
        }
        
        self._python_logger.info(
            f"Enhanced EKS Logger initialized for service '{self.service_name}' "
            f"in namespace '{self.namespace}' with components: {components_status}"
        )
    
    def _create_enhanced_log_entry(self, level: str, message: str, 
                                 correlation_id: Optional[str] = None,
                                 **kwargs) -> EnhancedLogEntry:
        """Create enhanced log entry with all available context"""
        # Get current timestamp
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Collect metadata
        kubernetes_metadata = {}
        if self._metadata_collector:
            try:
                kubernetes_metadata = self._metadata_collector.collect_all_metadata()
            except Exception as e:
                self._python_logger.debug(f"Failed to collect Kubernetes metadata: {e}")
        
        # Collect performance metrics
        performance_metrics = {}
        if self._performance_monitor:
            try:
                current_metrics = self._performance_monitor.collect_system_metrics()
                if current_metrics:
                    performance_metrics = current_metrics.to_dict()
            except Exception as e:
                self._python_logger.debug(f"Failed to collect performance metrics: {e}")
        
        # Collect security context
        security_context = {}
        if self._security_logger:
            try:
                security_context = self._security_logger.get_current_security_context()
            except Exception as e:
                self._python_logger.debug(f"Failed to collect security context: {e}")
        
        # Get sampling metadata
        sampling_metadata = {}
        if self._sampling_engine:
            try:
                sampling_metadata = self._sampling_engine.get_sampling_metadata()
            except Exception as e:
                self._python_logger.debug(f"Failed to get sampling metadata: {e}")
        
        # Create enhanced log entry
        return EnhancedLogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            service=self.service_name,
            namespace=self.namespace,
            correlation_id=correlation_id,
            kubernetes_metadata=kubernetes_metadata,
            performance_metrics=performance_metrics,
            security_context=security_context,
            sampling_metadata=sampling_metadata,
            custom_fields=kwargs
        )
    
    def _should_log(self, level: str, logger_name: str = None) -> bool:
        """Determine if log should be processed based on sampling"""
        if not self._sampling_engine:
            return True
        
        try:
            return self._sampling_engine.should_sample(level, logger_name or self.service_name)
        except Exception as e:
            self._python_logger.debug(f"Sampling decision failed: {e}")
            return True  # Default to logging on error
    
    def _process_log_entry(self, log_entry: EnhancedLogEntry) -> None:
        """Process log entry through buffer manager"""
        if not self._buffer_manager:
            # Fallback to Python logger
            self._python_logger.log(
                getattr(logging, log_entry.level, logging.INFO),
                f"[{log_entry.service}] {log_entry.message}"
            )
            return
        
        try:
            self._buffer_manager.add_log_entry(log_entry)
        except Exception as e:
            self._python_logger.error(f"Failed to process log entry: {e}")
            # Fallback to Python logger
            self._python_logger.log(
                getattr(logging, log_entry.level, logging.INFO),
                f"[{log_entry.service}] {log_entry.message}"
            )
    
    # Enhanced logging methods implementation
    def info(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log info message with enhanced context"""
        if not self._should_log("INFO"):
            return
        
        log_entry = self._create_enhanced_log_entry("INFO", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def debug(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log debug message with enhanced context"""
        if not self._should_log("DEBUG"):
            return
        
        log_entry = self._create_enhanced_log_entry("DEBUG", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def warning(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log warning message with enhanced context"""
        if not self._should_log("WARNING"):
            return
        
        log_entry = self._create_enhanced_log_entry("WARNING", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def warn(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Alias for warning method"""
        self.warning(msg, correlation_id, **kwargs)
    
    def error(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log error message with enhanced context"""
        # Error logs are always processed (sampling preserves errors)
        log_entry = self._create_enhanced_log_entry("ERROR", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def critical(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log critical message with enhanced context"""
        # Critical logs are always processed (sampling preserves critical)
        log_entry = self._create_enhanced_log_entry("CRITICAL", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    # Tracing methods implementation
    def start_trace(self, operation_name: str) -> str:
        """Start a new trace and return correlation ID"""
        if not self._tracing_manager:
            # Generate simple correlation ID as fallback
            import uuid
            return f"{self.service_name}-{uuid.uuid4().hex[:8]}"
        
        try:
            return self._tracing_manager.start_trace(operation_name)
        except Exception as e:
            self._python_logger.debug(f"Failed to start trace: {e}")
            # Generate simple correlation ID as fallback
            import uuid
            return f"{self.service_name}-{uuid.uuid4().hex[:8]}"
    
    def end_trace(self, correlation_id: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """End a trace with optional metadata"""
        if not self._tracing_manager:
            return
        
        try:
            # Log metadata if provided
            if metadata:
                self._python_logger.debug(f"Trace metadata: {metadata}", extra={
                    'correlation_id': correlation_id,
                    'metadata': metadata
                })
            
            # Call tracing manager without metadata parameter (it doesn't support it)
            self._tracing_manager.end_trace(correlation_id, success)
        except Exception as e:
            self._python_logger.debug(f"Failed to end trace: {e}")
    
    # Performance monitoring methods implementation
    def log_performance_metrics(self) -> None:
        """Log current performance metrics"""
        if not self._performance_monitor:
            return
        
        try:
            metrics = self._performance_monitor.collect_system_metrics()
            if metrics:
                self.info("Performance metrics collected", 
                         event_type="performance_metrics",
                         metrics=metrics.to_dict())
        except Exception as e:
            self._python_logger.debug(f"Failed to log performance metrics: {e}")
    
    # Health monitoring methods implementation
    def get_health_status(self) -> HealthStatus:
        """Get logging system health status"""
        if not self._health_monitor:
            # Return basic healthy status
            status = HealthStatus(state=HealthState.HEALTHY)
            status.add_alert("Health monitoring disabled")
            return status
        
        try:
            return self._health_monitor.get_health_status()
        except Exception as e:
            self._python_logger.debug(f"Failed to get health status: {e}")
            status = HealthStatus(state=HealthState.UNHEALTHY)
            status.add_alert(f"Health check failed: {e}")
            return status
    
    # Configuration methods implementation
    def configure_sampling(self, config: Dict[str, Any]) -> None:
        """Configure log sampling parameters"""
        if not self._sampling_engine:
            return
        
        try:
            self._sampling_engine.update_configuration(config)
            self.info("Sampling configuration updated", 
                     event_type="configuration_change",
                     config_type="sampling",
                     new_config=config)
        except Exception as e:
            self.error(f"Failed to update sampling configuration: {e}",
                      event_type="configuration_error",
                      config_type="sampling")
    
    # Additional utility methods
    def flush_logs(self) -> None:
        """Manually flush all buffered logs"""
        if self._buffer_manager:
            try:
                self._buffer_manager.flush_all()
            except Exception as e:
                self._python_logger.error(f"Failed to flush logs: {e}")
    
    def get_component_status(self) -> Dict[str, Any]:
        """Get status of all components"""
        return {
            'initialized': self._initialized,
            'components': {
                'tracing': {
                    'enabled': self.enable_tracing,
                    'available': self._tracing_manager is not None
                },
                'metadata': {
                    'enabled': self.enable_kubernetes_metadata,
                    'available': self._metadata_collector is not None
                },
                'performance': {
                    'enabled': self.enable_performance_monitoring,
                    'available': self._performance_monitor is not None
                },
                'sampling': {
                    'enabled': self.enable_sampling,
                    'available': self._sampling_engine is not None
                },
                'security': {
                    'enabled': self.enable_security_logging,
                    'available': self._security_logger is not None
                },
                'health': {
                    'enabled': self.enable_health_monitoring,
                    'available': self._health_monitor is not None
                },
                'cloudwatch': {
                    'enabled': self.enable_cloudwatch,
                    'available': self._cloudwatch_handler is not None
                },
                'buffer': {
                    'enabled': True,  # Always enabled
                    'available': self._buffer_manager is not None
                }
            }
        }
    
    def shutdown(self) -> None:
        """Gracefully shutdown the logger and all components"""
        with self._lock:
            try:
                # Flush any remaining logs
                self.flush_logs()
                
                # Shutdown components
                if self._buffer_manager:
                    self._buffer_manager.shutdown()
                
                if self._performance_monitor:
                    self._performance_monitor.stop_monitoring()
                
                if self._health_monitor:
                    self._health_monitor.stop()
                
                self.info("Enhanced EKS Logger shutdown completed")
                
            except Exception as e:
                self._python_logger.error(f"Error during shutdown: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()