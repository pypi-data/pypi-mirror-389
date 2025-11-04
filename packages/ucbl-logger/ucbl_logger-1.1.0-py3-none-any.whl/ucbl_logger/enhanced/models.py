"""
Data models for enhanced EKS logging components

These models define the data structures used throughout the enhanced logging system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time


# Enums are now imported from component-specific modules


# Core models are now in component-specific modules
# Import them here for backward compatibility
from .tracing.models import TraceContext
from .sampling.models import SamplingConfig, SamplingDecision, SamplingStrategy
from .buffering.models import BufferConfig
from .performance.models import PerformanceThresholds, SystemMetrics
from .health.models import HealthStatus, HealthState
from .metadata.models import KubernetesMetadata
from .security.models import SecurityContext


@dataclass
class EnhancedLogEntry:
    """Enhanced log entry with all metadata"""
    timestamp: str
    level: str
    message: str
    service: str
    namespace: str = "default"
    pod_name: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    kubernetes_metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Optional[Dict[str, Any]] = None
    sampling_metadata: Optional[Dict[str, Any]] = None
    security_context: Optional[Dict[str, Any]] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'timestamp': self.timestamp,
            'level': self.level,
            'message': self.message,
            'service': self.service,
            'namespace': self.namespace
        }
        
        # Add optional fields if present
        if self.pod_name:
            result['pod_name'] = self.pod_name
        if self.correlation_id:
            result['correlation_id'] = self.correlation_id
        if self.trace_id:
            result['trace_id'] = self.trace_id
        if self.span_id:
            result['span_id'] = self.span_id
        if self.kubernetes_metadata:
            result['kubernetes'] = self.kubernetes_metadata
        if self.performance_metrics:
            result['performance'] = self.performance_metrics
        if self.sampling_metadata:
            result['sampling'] = self.sampling_metadata
        if self.security_context:
            result['security'] = self.security_context
        if self.custom_fields:
            result.update(self.custom_fields)
            
        return result


# Models are now imported from component-specific modules