"""
Interfaces for distributed tracing components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .models import TraceContext


class ITracingManager(ABC):
    """Interface for distributed tracing management"""
    
    @abstractmethod
    def generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for request tracking"""
        pass
    
    @abstractmethod
    def start_span(self, operation_name: str, parent_id: Optional[str] = None) -> str:
        """Start a new trace span and return correlation ID"""
        pass
    
    @abstractmethod
    def start_child_span(self, operation_name: str, parent_correlation_id: Optional[str] = None) -> str:
        """Start a child span from current or specified parent"""
        pass
    
    @abstractmethod
    def end_span(self, correlation_id: str, success: bool = True) -> None:
        """End a trace span"""
        pass
    
    @abstractmethod
    def get_trace_context(self, correlation_id: str) -> Optional[TraceContext]:
        """Get trace context for a correlation ID"""
        pass
    
    @abstractmethod
    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from thread-local storage"""
        pass
    
    @abstractmethod
    def set_current_correlation_id(self, correlation_id: str) -> None:
        """Set current correlation ID in thread-local storage"""
        pass
    
    @abstractmethod
    def propagate_context_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract correlation ID from HTTP headers"""
        pass
    
    @abstractmethod
    def inject_context_to_headers(self, correlation_id: str, headers: Dict[str, str]) -> None:
        """Inject correlation ID into HTTP headers"""
        pass
    
    @abstractmethod
    def cleanup_finished_traces(self, max_age_seconds: int = 3600) -> None:
        """Clean up old finished traces to prevent memory leaks"""
        pass