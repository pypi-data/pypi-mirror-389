"""
Base implementation for distributed tracing components
"""

import uuid
import time
import threading
from typing import Dict, Any, Optional
from .interfaces import ITracingManager
from .models import TraceContext
from .propagation import TraceContextPropagator


class TracingManager(ITracingManager):
    """Enhanced tracing manager with thread-local storage and correlation ID propagation"""
    
    def __init__(self, service_name: str, enable_opentelemetry: bool = False):
        self.service_name = service_name
        self.enable_otel = enable_opentelemetry
        self.active_traces: Dict[str, TraceContext] = {}
        self._local = threading.local()
    
    def generate_correlation_id(self) -> str:
        """Generate a unique correlation ID with service prefix"""
        # Use UUID4 for uniqueness with service prefix
        unique_id = uuid.uuid4().hex[:12]  # 12 characters for better uniqueness
        return f"{self.service_name}-{unique_id}"
    
    def start_span(self, operation_name: str, parent_id: Optional[str] = None) -> str:
        """Start a new trace span and return correlation ID"""
        correlation_id = self.generate_correlation_id()
        
        # Determine trace_id and parent_span_id
        trace_id = correlation_id
        parent_span_id = None
        
        if parent_id:
            parent_context = self.get_trace_context(parent_id)
            if parent_context:
                trace_id = parent_context.trace_id or parent_context.correlation_id
                parent_span_id = parent_context.span_id
        
        # Generate proper hex IDs for W3C compatibility
        span_id = uuid.uuid4().hex[:16]  # 16 hex chars for span ID
        
        # Ensure trace_id is valid hex for W3C format
        if self.enable_otel:
            import hashlib
            trace_id = hashlib.md5(trace_id.encode()).hexdigest()  # 32 hex chars
        
        # Create trace context
        trace_context = TraceContext(
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time()
        )
        
        # Store in active traces
        self.active_traces[correlation_id] = trace_context
        
        # Set in thread-local storage for automatic propagation
        self._set_current_correlation_id(correlation_id)
        
        return correlation_id
    
    def start_child_span(self, operation_name: str, parent_correlation_id: Optional[str] = None) -> str:
        """Start a child span from current or specified parent"""
        if not parent_correlation_id:
            parent_correlation_id = self.get_current_correlation_id()
        
        return self.start_span(operation_name, parent_correlation_id)
    
    def end_span(self, correlation_id: str, success: bool = True) -> None:
        """End a trace span"""
        if correlation_id in self.active_traces:
            trace_context = self.active_traces[correlation_id]
            trace_context.end_time = time.time()
            trace_context.success = success
            
            # Clear from thread-local if it's the current one
            current_id = self._get_current_correlation_id()
            if current_id == correlation_id:
                self._clear_current_correlation_id()
    
    def get_trace_context(self, correlation_id: str) -> Optional[TraceContext]:
        """Get trace context for a correlation ID"""
        return self.active_traces.get(correlation_id)
    
    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from thread-local storage"""
        return self._get_current_correlation_id()
    
    def set_current_correlation_id(self, correlation_id: str) -> None:
        """Set current correlation ID in thread-local storage"""
        self._set_current_correlation_id(correlation_id)
    
    def propagate_context_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract correlation ID from HTTP headers"""
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        
        if correlation_id:
            # Set in thread-local storage for automatic propagation
            self._set_current_correlation_id(correlation_id)
            
            # If OpenTelemetry is enabled, also extract W3C trace context
            if self.enable_otel:
                trace_context_data = TraceContextPropagator.extract_trace_context(headers)
                if trace_context_data:
                    version, trace_id, span_id, flags = trace_context_data
                    
                    # Create or update trace context with W3C data
                    if correlation_id not in self.active_traces:
                        trace_context = TraceContext(
                            correlation_id=correlation_id,
                            trace_id=trace_id,
                            span_id=span_id,
                            operation_name="incoming_request"
                        )
                        self.active_traces[correlation_id] = trace_context
                    else:
                        # Update existing context
                        existing_context = self.active_traces[correlation_id]
                        existing_context.trace_id = trace_id
                        existing_context.span_id = span_id
        
        return correlation_id
    
    def inject_context_to_headers(self, correlation_id: str, headers: Dict[str, str]) -> None:
        """Inject correlation ID into HTTP headers"""
        # Always inject correlation ID
        TraceContextPropagator.inject_correlation_id(correlation_id, headers)
        
        # Add W3C Trace Context if OpenTelemetry is enabled
        if self.enable_otel:
            trace_context = self.get_trace_context(correlation_id)
            if trace_context and trace_context.trace_id and trace_context.span_id:
                TraceContextPropagator.inject_w3c_trace_context(
                    trace_context.trace_id, 
                    trace_context.span_id, 
                    headers=headers
                )
    
    def cleanup_finished_traces(self, max_age_seconds: int = 3600) -> None:
        """Clean up old finished traces to prevent memory leaks"""
        current_time = time.time()
        to_remove = []
        
        for correlation_id, trace_context in self.active_traces.items():
            if (trace_context.end_time and 
                current_time - trace_context.end_time > max_age_seconds):
                to_remove.append(correlation_id)
        
        for correlation_id in to_remove:
            del self.active_traces[correlation_id]
    
    def _get_current_correlation_id(self) -> Optional[str]:
        """Get correlation ID from thread-local storage"""
        return getattr(self._local, 'correlation_id', None)
    
    def _set_current_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID in thread-local storage"""
        self._local.correlation_id = correlation_id
    
    def _clear_current_correlation_id(self) -> None:
        """Clear correlation ID from thread-local storage"""
        if hasattr(self._local, 'correlation_id'):
            delattr(self._local, 'correlation_id')


# Maintain backward compatibility
BaseTracingManager = TracingManager