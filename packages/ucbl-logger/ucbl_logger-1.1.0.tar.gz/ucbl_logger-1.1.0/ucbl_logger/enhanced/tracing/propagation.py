"""
HTTP header propagation utilities for distributed tracing
"""

import re
from typing import Dict, Optional, Tuple


class TraceContextPropagator:
    """Handles W3C Trace Context and custom header propagation"""
    
    # W3C Trace Context header names
    TRACEPARENT_HEADER = 'traceparent'
    TRACESTATE_HEADER = 'tracestate'
    
    # Custom correlation headers (in order of preference)
    CORRELATION_HEADERS = [
        'X-Correlation-ID',
        'X-Trace-ID', 
        'Correlation-ID',
        'X-Request-ID'
    ]
    
    # W3C traceparent format: version-trace_id-span_id-flags
    TRACEPARENT_PATTERN = re.compile(r'^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$')
    
    @classmethod
    def extract_correlation_id(cls, headers: Dict[str, str]) -> Optional[str]:
        """Extract correlation ID from HTTP headers"""
        # First try custom correlation headers
        for header_name in cls.CORRELATION_HEADERS:
            correlation_id = cls._get_header_case_insensitive(headers, header_name)
            if correlation_id:
                return correlation_id
        
        # Try W3C traceparent
        traceparent = cls._get_header_case_insensitive(headers, cls.TRACEPARENT_HEADER)
        if traceparent:
            trace_context = cls._parse_traceparent(traceparent)
            if trace_context:
                # Use trace_id as correlation_id for W3C context
                return trace_context[1]
        
        return None
    
    @classmethod
    def extract_trace_context(cls, headers: Dict[str, str]) -> Optional[Tuple[str, str, str, str]]:
        """Extract W3C trace context from headers"""
        traceparent = cls._get_header_case_insensitive(headers, cls.TRACEPARENT_HEADER)
        if traceparent:
            return cls._parse_traceparent(traceparent)
        return None
    
    @classmethod
    def inject_correlation_id(cls, correlation_id: str, headers: Dict[str, str]) -> None:
        """Inject correlation ID into HTTP headers"""
        headers['X-Correlation-ID'] = correlation_id
        headers['X-Trace-ID'] = correlation_id
    
    @classmethod
    def inject_w3c_trace_context(cls, trace_id: str, span_id: str, 
                                flags: str = '01', headers: Dict[str, str] = None) -> Dict[str, str]:
        """Inject W3C trace context into headers"""
        if headers is None:
            headers = {}
        
        # Ensure proper formatting
        trace_id_formatted = trace_id.zfill(32)[:32]
        span_id_formatted = span_id.zfill(16)[:16]
        
        # Create traceparent header
        traceparent = f"00-{trace_id_formatted}-{span_id_formatted}-{flags}"
        headers[cls.TRACEPARENT_HEADER] = traceparent
        
        return headers
    
    @classmethod
    def inject_full_context(cls, correlation_id: str, trace_id: Optional[str] = None, 
                           span_id: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Inject both correlation ID and W3C trace context"""
        if headers is None:
            headers = {}
        
        # Inject correlation ID
        cls.inject_correlation_id(correlation_id, headers)
        
        # Inject W3C context if available
        if trace_id and span_id:
            cls.inject_w3c_trace_context(trace_id, span_id, headers=headers)
        
        return headers
    
    @classmethod
    def _get_header_case_insensitive(cls, headers: Dict[str, str], header_name: str) -> Optional[str]:
        """Get header value with case-insensitive lookup"""
        for key, value in headers.items():
            if key.lower() == header_name.lower():
                return value
        return None
    
    @classmethod
    def _parse_traceparent(cls, traceparent: str) -> Optional[Tuple[str, str, str, str]]:
        """Parse W3C traceparent header"""
        match = cls.TRACEPARENT_PATTERN.match(traceparent.strip())
        if match:
            version, trace_id, span_id, flags = match.groups()
            return version, trace_id, span_id, flags
        return None
    
    @classmethod
    def create_child_span_context(cls, parent_trace_id: str, parent_span_id: str, 
                                 new_span_id: str) -> Tuple[str, str]:
        """Create child span context from parent"""
        return parent_trace_id, new_span_id
    
    @classmethod
    def is_valid_trace_id(cls, trace_id: str) -> bool:
        """Validate trace ID format"""
        if not trace_id or len(trace_id) > 32:
            return False
        try:
            int(trace_id, 16)
            return trace_id != '0' * len(trace_id)  # Not all zeros
        except ValueError:
            return False
    
    @classmethod
    def is_valid_span_id(cls, span_id: str) -> bool:
        """Validate span ID format"""
        if not span_id or len(span_id) > 16:
            return False
        try:
            int(span_id, 16)
            return span_id != '0' * len(span_id)  # Not all zeros
        except ValueError:
            return False