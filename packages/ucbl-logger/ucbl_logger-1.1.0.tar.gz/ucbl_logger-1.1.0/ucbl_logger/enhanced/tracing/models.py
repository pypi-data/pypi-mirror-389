"""
Data models for distributed tracing
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time


@dataclass
class TraceContext:
    """Context information for distributed tracing"""
    correlation_id: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate duration in milliseconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if trace span is finished"""
        return self.end_time is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace context to dictionary for logging"""
        result = {
            'correlation_id': self.correlation_id,
            'operation_name': self.operation_name,
            'start_time': self.start_time,
            'success': self.success
        }
        
        if self.trace_id:
            result['trace_id'] = self.trace_id
        if self.span_id:
            result['span_id'] = self.span_id
        if self.parent_span_id:
            result['parent_span_id'] = self.parent_span_id
        if self.end_time:
            result['end_time'] = self.end_time
            result['duration_ms'] = self.duration_ms
        if self.metadata:
            result['metadata'] = self.metadata
            
        return result