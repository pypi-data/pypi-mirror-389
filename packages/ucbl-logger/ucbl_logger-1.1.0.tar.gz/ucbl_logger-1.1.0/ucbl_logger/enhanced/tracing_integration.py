"""
Tracing integration for enhanced logging methods

This module provides the concrete implementation that integrates distributed tracing
with the existing logging methods while maintaining backward compatibility.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from .enhanced_eks_logger import EnhancedEKSLoggerBase
from .tracing.base import TracingManager
from .metadata.base import BaseMetadataCollector
from .performance.base import BasePerformanceMonitor
from .sampling.base import BaseSamplingEngine
from .buffering.base import BaseBufferManager
from .health.base import BaseHealthMonitor
from .security.base import BaseSecurityContextLogger
from .models import EnhancedLogEntry
from .health.models import HealthStatus


class TracingIntegratedLogger(EnhancedEKSLoggerBase):
    """
    Enhanced EKS Logger with integrated distributed tracing
    
    This implementation provides full tracing integration with all logging methods
    while maintaining backward compatibility with existing UCBLLogger API.
    """
    
    def __init__(self, 
                 service_name: str,
                 namespace: str = "default",
                 enable_tracing: bool = True,
                 enable_performance_monitoring: bool = True,
                 enable_kubernetes_metadata: bool = True,
                 enable_sampling: bool = True,
                 enable_security_logging: bool = True,
                 enable_opentelemetry: bool = False,
                 **kwargs):
        """Initialize the tracing-integrated logger"""
        super().__init__(
            service_name=service_name,
            namespace=namespace,
            enable_tracing=enable_tracing,
            enable_performance_monitoring=enable_performance_monitoring,
            enable_kubernetes_metadata=enable_kubernetes_metadata,
            enable_sampling=enable_sampling,
            enable_security_logging=enable_security_logging,
            **kwargs
        )
        
        # Initialize components
        self._initialize_components(enable_opentelemetry)
    
    def _initialize_components(self, enable_opentelemetry: bool = False) -> None:
        """Initialize all enhanced components"""
        # Initialize tracing manager
        if self.enable_tracing:
            self._tracing_manager = TracingManager(
                service_name=self.service_name,
                enable_opentelemetry=enable_opentelemetry
            )
        
        # Initialize other components (placeholder implementations)
        if self.enable_kubernetes_metadata:
            self._metadata_collector = BaseMetadataCollector()
        
        if self.enable_performance_monitoring:
            self._performance_monitor = BasePerformanceMonitor()
        
        if self.enable_sampling:
            self._sampling_engine = BaseSamplingEngine(self.sampling_config)
        
        self._buffer_manager = BaseBufferManager(self.buffer_config)
        self._health_monitor = BaseHealthMonitor()
        
        if self.enable_security_logging:
            self._security_logger = BaseSecurityContextLogger()
    
    def _create_enhanced_log_entry(self, level: str, message: str, 
                                  correlation_id: Optional[str] = None,
                                  **kwargs) -> EnhancedLogEntry:
        """Create an enhanced log entry with all metadata"""
        # Get or create correlation ID
        if correlation_id is None and self.enable_tracing and self._tracing_manager:
            correlation_id = self._tracing_manager.get_current_correlation_id()
        
        # Get trace context if available
        trace_id = None
        span_id = None
        if correlation_id and self._tracing_manager:
            trace_context = self._tracing_manager.get_trace_context(correlation_id)
            if trace_context:
                trace_id = trace_context.trace_id
                span_id = trace_context.span_id
        
        # Collect metadata
        kubernetes_metadata = {}
        if self.enable_kubernetes_metadata and self._metadata_collector:
            try:
                kubernetes_metadata = self._metadata_collector.collect_pod_metadata()
            except Exception:
                # Fail gracefully if metadata collection fails
                pass
        
        # Collect performance metrics if requested
        performance_metrics = None
        if (self.enable_performance_monitoring and self._performance_monitor and 
            kwargs.get('include_performance_metrics', False)):
            try:
                performance_metrics = self._performance_monitor.collect_current_metrics()
            except Exception:
                # Fail gracefully if performance collection fails
                pass
        
        # Collect security context if enabled
        security_context = None
        if self.enable_security_logging and self._security_logger:
            try:
                security_context = self._security_logger.get_security_context()
            except Exception:
                # Fail gracefully if security context collection fails
                pass
        
        # Create enhanced log entry
        return EnhancedLogEntry(
            timestamp=datetime.now().astimezone().isoformat(),
            level=level,
            message=message,
            service=self.service_name,
            namespace=self.namespace,
            pod_name=kubernetes_metadata.get('pod_name'),
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            kubernetes_metadata=kubernetes_metadata,
            performance_metrics=performance_metrics,
            security_context=security_context,
            custom_fields=kwargs
        )
    
    def _should_log(self, level: str, logger_name: str = None) -> bool:
        """Determine if log should be processed based on sampling"""
        if not self.enable_sampling or not self._sampling_engine:
            return True
        
        try:
            return self._sampling_engine.should_sample(level, logger_name or self.service_name)
        except Exception:
            # If sampling fails, default to logging
            return True
    
    def _process_log_entry(self, log_entry: EnhancedLogEntry) -> None:
        """Process and output the log entry"""
        if not self._should_log(log_entry.level):
            return
        
        try:
            # Convert to JSON for output
            log_dict = log_entry.to_dict()
            log_json = json.dumps(log_dict, default=str)
            
            # Output to stdout (can be extended to support multiple outputs)
            print(log_json)
            
            # Buffer the log entry if buffering is enabled
            if self._buffer_manager:
                self._buffer_manager.add_log_entry(log_entry)
        
        except Exception as e:
            # Fallback to simple logging if enhanced processing fails
            fallback_message = f"{log_entry.timestamp} - {log_entry.level} - {log_entry.message}"
            if log_entry.correlation_id:
                fallback_message += f" [correlation_id={log_entry.correlation_id}]"
            print(fallback_message)
    
    # Enhanced logging methods with tracing integration
    def info(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log info message with enhanced context"""
        log_entry = self._create_enhanced_log_entry("INFO", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def debug(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log debug message with enhanced context"""
        log_entry = self._create_enhanced_log_entry("DEBUG", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def warning(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log warning message with enhanced context"""
        log_entry = self._create_enhanced_log_entry("WARNING", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def warn(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Alias for warning method"""
        self.warning(msg, correlation_id, **kwargs)
    
    def error(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log error message with enhanced context"""
        log_entry = self._create_enhanced_log_entry("ERROR", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    def critical(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log critical message with enhanced context"""
        log_entry = self._create_enhanced_log_entry("CRITICAL", msg, correlation_id, **kwargs)
        self._process_log_entry(log_entry)
    
    # Tracing methods
    def start_trace(self, operation_name: str) -> str:
        """Start a new trace and return correlation ID"""
        if not self.enable_tracing or not self._tracing_manager:
            # Generate a simple correlation ID if tracing is disabled
            import uuid
            return f"{self.service_name}-{uuid.uuid4().hex[:8]}"
        
        correlation_id = self._tracing_manager.start_span(operation_name)
        
        # Log trace start
        self.debug(f"Trace started: {operation_name}", 
                  correlation_id=correlation_id,
                  event_type="trace_start",
                  operation_name=operation_name)
        
        return correlation_id
    
    def end_trace(self, correlation_id: str, success: bool = True) -> None:
        """End a trace"""
        if self.enable_tracing and self._tracing_manager:
            self._tracing_manager.end_span(correlation_id, success)
        
        # Log trace end
        self.debug(f"Trace ended: {correlation_id}", 
                  correlation_id=correlation_id,
                  event_type="trace_end",
                  success=success)
    
    def start_child_trace(self, operation_name: str, parent_correlation_id: Optional[str] = None) -> str:
        """Start a child trace"""
        if not self.enable_tracing or not self._tracing_manager:
            return self.start_trace(operation_name)
        
        correlation_id = self._tracing_manager.start_child_span(operation_name, parent_correlation_id)
        
        # Log child trace start
        self.debug(f"Child trace started: {operation_name}", 
                  correlation_id=correlation_id,
                  event_type="child_trace_start",
                  operation_name=operation_name,
                  parent_correlation_id=parent_correlation_id)
        
        return correlation_id
    
    # Header propagation methods
    def extract_trace_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract trace context from HTTP headers"""
        if not self.enable_tracing or not self._tracing_manager:
            return None
        
        correlation_id = self._tracing_manager.propagate_context_from_headers(headers)
        
        if correlation_id:
            self.debug("Trace context extracted from headers", 
                      correlation_id=correlation_id,
                      event_type="trace_extracted")
        
        return correlation_id
    
    def inject_trace_to_headers(self, correlation_id: str, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Inject trace context into HTTP headers"""
        if headers is None:
            headers = {}
        
        if self.enable_tracing and self._tracing_manager:
            self._tracing_manager.inject_context_to_headers(correlation_id, headers)
            
            self.debug("Trace context injected to headers", 
                      correlation_id=correlation_id,
                      event_type="trace_injected")
        
        return headers
    
    # Performance monitoring methods
    def log_performance_metrics(self) -> None:
        """Log current performance metrics"""
        if not self.enable_performance_monitoring or not self._performance_monitor:
            return
        
        try:
            metrics = self._performance_monitor.collect_current_metrics()
            self.info("Performance metrics collected", 
                     include_performance_metrics=True,
                     event_type="performance_metrics",
                     **metrics)
        except Exception as e:
            self.error(f"Failed to collect performance metrics: {e}",
                      event_type="performance_collection_error")
    
    # Health monitoring methods
    def get_health_status(self) -> HealthStatus:
        """Get logging system health status"""
        if not self._health_monitor:
            return HealthStatus(healthy=True, message="Health monitoring disabled")
        
        try:
            return self._health_monitor.get_health_status()
        except Exception as e:
            return HealthStatus(healthy=False, message=f"Health check failed: {e}")
    
    # Configuration methods
    def configure_sampling(self, config: Dict[str, Any]) -> None:
        """Configure log sampling parameters"""
        if self.enable_sampling and self._sampling_engine:
            try:
                self._sampling_engine.update_configuration(config)
                self.info("Sampling configuration updated", 
                         event_type="config_update",
                         config_type="sampling",
                         config=config)
            except Exception as e:
                self.error(f"Failed to update sampling configuration: {e}",
                          event_type="config_update_error")
    
    # Utility methods
    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from thread-local storage"""
        if self.enable_tracing and self._tracing_manager:
            return self._tracing_manager.get_current_correlation_id()
        return None
    
    def set_current_correlation_id(self, correlation_id: str) -> None:
        """Set current correlation ID in thread-local storage"""
        if self.enable_tracing and self._tracing_manager:
            self._tracing_manager.set_current_correlation_id(correlation_id)
    
    def cleanup_old_traces(self, max_age_seconds: int = 3600) -> None:
        """Clean up old finished traces"""
        if self.enable_tracing and self._tracing_manager:
            self._tracing_manager.cleanup_finished_traces(max_age_seconds)
            self.debug("Old traces cleaned up", 
                      event_type="trace_cleanup",
                      max_age_seconds=max_age_seconds)