"""
Unit tests for distributed tracing components
"""

import unittest
import time
import threading
import uuid
from unittest.mock import Mock, MagicMock, patch

# Import tracing components
from ucbl_logger.enhanced.tracing import (
    ITracingManager,
    TraceContext,
    TracingManager,
    TraceContextPropagator
)
from ucbl_logger.enhanced.tracing_integration import TracingIntegratedLogger


class TestTraceContext(unittest.TestCase):
    """Test TraceContext model"""
    
    def test_trace_context_creation(self):
        """Test basic trace context creation"""
        correlation_id = "test-service-12345678"
        context = TraceContext(
            correlation_id=correlation_id,
            operation_name="test_operation"
        )
        
        self.assertEqual(context.correlation_id, correlation_id)
        self.assertEqual(context.operation_name, "test_operation")
        self.assertIsNone(context.trace_id)
        self.assertIsNone(context.span_id)
        self.assertIsNone(context.parent_span_id)
        self.assertTrue(context.success)
        self.assertIsNone(context.end_time)
        self.assertFalse(context.is_finished)
    
    def test_trace_context_with_all_fields(self):
        """Test trace context with all fields populated"""
        context = TraceContext(
            correlation_id="test-12345678",
            trace_id="abcd1234",
            span_id="efgh5678",
            parent_span_id="ijkl9012",
            operation_name="complex_operation",
            start_time=1000.0,
            end_time=1005.0,
            success=False,
            metadata={"key": "value"}
        )
        
        self.assertEqual(context.correlation_id, "test-12345678")
        self.assertEqual(context.trace_id, "abcd1234")
        self.assertEqual(context.span_id, "efgh5678")
        self.assertEqual(context.parent_span_id, "ijkl9012")
        self.assertEqual(context.operation_name, "complex_operation")
        self.assertEqual(context.start_time, 1000.0)
        self.assertEqual(context.end_time, 1005.0)
        self.assertFalse(context.success)
        self.assertEqual(context.metadata, {"key": "value"})
        self.assertTrue(context.is_finished)
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        context = TraceContext(
            correlation_id="test-12345678",
            start_time=1000.0,
            end_time=1005.5
        )
        
        self.assertEqual(context.duration_ms, 5500.0)
        
        # Test with no end time
        context.end_time = None
        self.assertIsNone(context.duration_ms)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        context = TraceContext(
            correlation_id="test-12345678",
            trace_id="abcd1234",
            span_id="efgh5678",
            operation_name="test_operation",
            start_time=1000.0,
            end_time=1005.0,
            success=True,
            metadata={"key": "value"}
        )
        
        result = context.to_dict()
        
        self.assertEqual(result["correlation_id"], "test-12345678")
        self.assertEqual(result["trace_id"], "abcd1234")
        self.assertEqual(result["span_id"], "efgh5678")
        self.assertEqual(result["operation_name"], "test_operation")
        self.assertEqual(result["start_time"], 1000.0)
        self.assertEqual(result["end_time"], 1005.0)
        self.assertEqual(result["duration_ms"], 5000.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"], {"key": "value"})


class TestTraceContextPropagator(unittest.TestCase):
    """Test TraceContextPropagator functionality"""
    
    def test_extract_correlation_id_from_custom_headers(self):
        """Test extracting correlation ID from custom headers"""
        # Test X-Correlation-ID
        headers = {"X-Correlation-ID": "test-12345678"}
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        self.assertEqual(correlation_id, "test-12345678")
        
        # Test X-Trace-ID
        headers = {"X-Trace-ID": "trace-87654321"}
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        self.assertEqual(correlation_id, "trace-87654321")
        
        # Test case insensitive
        headers = {"x-correlation-id": "lowercase-12345"}
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        self.assertEqual(correlation_id, "lowercase-12345")
    
    def test_extract_correlation_id_from_w3c_traceparent(self):
        """Test extracting correlation ID from W3C traceparent header"""
        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        self.assertEqual(correlation_id, "0af7651916cd43dd8448eb211c80319c")
    
    def test_extract_correlation_id_priority(self):
        """Test header priority when multiple headers are present"""
        headers = {
            "X-Correlation-ID": "custom-correlation",
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        # Custom headers should take priority over W3C
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        self.assertEqual(correlation_id, "custom-correlation")
    
    def test_extract_correlation_id_no_headers(self):
        """Test extracting correlation ID when no relevant headers present"""
        headers = {"Content-Type": "application/json"}
        correlation_id = TraceContextPropagator.extract_correlation_id(headers)
        self.assertIsNone(correlation_id)
    
    def test_extract_trace_context(self):
        """Test extracting W3C trace context"""
        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        trace_context = TraceContextPropagator.extract_trace_context(headers)
        
        self.assertIsNotNone(trace_context)
        version, trace_id, span_id, flags = trace_context
        self.assertEqual(version, "00")
        self.assertEqual(trace_id, "0af7651916cd43dd8448eb211c80319c")
        self.assertEqual(span_id, "b7ad6b7169203331")
        self.assertEqual(flags, "01")
    
    def test_extract_trace_context_invalid(self):
        """Test extracting invalid W3C trace context"""
        headers = {"traceparent": "invalid-format"}
        trace_context = TraceContextPropagator.extract_trace_context(headers)
        self.assertIsNone(trace_context)
    
    def test_inject_correlation_id(self):
        """Test injecting correlation ID into headers"""
        headers = {}
        TraceContextPropagator.inject_correlation_id("test-12345678", headers)
        
        self.assertEqual(headers["X-Correlation-ID"], "test-12345678")
        self.assertEqual(headers["X-Trace-ID"], "test-12345678")
    
    def test_inject_w3c_trace_context(self):
        """Test injecting W3C trace context"""
        headers = {}
        TraceContextPropagator.inject_w3c_trace_context(
            "0af7651916cd43dd8448eb211c80319c",
            "b7ad6b7169203331",
            headers=headers
        )
        
        expected_traceparent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        self.assertEqual(headers["traceparent"], expected_traceparent)
    
    def test_inject_w3c_trace_context_with_padding(self):
        """Test injecting W3C trace context with proper padding"""
        headers = {}
        TraceContextPropagator.inject_w3c_trace_context(
            "abc123",  # Short trace ID
            "def456",  # Short span ID
            headers=headers
        )
        
        expected_traceparent = "00-00000000000000000000000000abc123-0000000000def456-01"
        self.assertEqual(headers["traceparent"], expected_traceparent)
    
    def test_inject_full_context(self):
        """Test injecting full context (correlation ID + W3C)"""
        headers = {}
        result_headers = TraceContextPropagator.inject_full_context(
            "test-12345678",
            "0af7651916cd43dd8448eb211c80319c",
            "b7ad6b7169203331",
            headers
        )
        
        self.assertEqual(result_headers["X-Correlation-ID"], "test-12345678")
        self.assertEqual(result_headers["X-Trace-ID"], "test-12345678")
        self.assertIn("traceparent", result_headers)
    
    def test_create_child_span_context(self):
        """Test creating child span context"""
        parent_trace_id = "0af7651916cd43dd8448eb211c80319c"
        parent_span_id = "b7ad6b7169203331"
        new_span_id = "c8be7c8e72094567"
        
        trace_id, span_id = TraceContextPropagator.create_child_span_context(
            parent_trace_id, parent_span_id, new_span_id
        )
        
        self.assertEqual(trace_id, parent_trace_id)
        self.assertEqual(span_id, new_span_id)
    
    def test_validate_trace_id(self):
        """Test trace ID validation"""
        # Valid trace IDs
        self.assertTrue(TraceContextPropagator.is_valid_trace_id("0af7651916cd43dd8448eb211c80319c"))
        self.assertTrue(TraceContextPropagator.is_valid_trace_id("abc123"))
        
        # Invalid trace IDs
        self.assertFalse(TraceContextPropagator.is_valid_trace_id(""))
        self.assertFalse(TraceContextPropagator.is_valid_trace_id("00000000000000000000000000000000"))
        self.assertFalse(TraceContextPropagator.is_valid_trace_id("invalid-hex"))
        self.assertFalse(TraceContextPropagator.is_valid_trace_id("a" * 33))  # Too long
    
    def test_validate_span_id(self):
        """Test span ID validation"""
        # Valid span IDs
        self.assertTrue(TraceContextPropagator.is_valid_span_id("b7ad6b7169203331"))
        self.assertTrue(TraceContextPropagator.is_valid_span_id("abc123"))
        
        # Invalid span IDs
        self.assertFalse(TraceContextPropagator.is_valid_span_id(""))
        self.assertFalse(TraceContextPropagator.is_valid_span_id("0000000000000000"))
        self.assertFalse(TraceContextPropagator.is_valid_span_id("invalid-hex"))
        self.assertFalse(TraceContextPropagator.is_valid_span_id("a" * 17))  # Too long


class TestTracingManager(unittest.TestCase):
    """Test TracingManager functionality"""
    
    def setUp(self):
        self.manager = TracingManager("test-service")
    
    def test_initialization(self):
        """Test tracing manager initialization"""
        self.assertEqual(self.manager.service_name, "test-service")
        self.assertFalse(self.manager.enable_otel)
        self.assertEqual(len(self.manager.active_traces), 0)
    
    def test_initialization_with_opentelemetry(self):
        """Test tracing manager initialization with OpenTelemetry"""
        manager = TracingManager("test-service", enable_opentelemetry=True)
        self.assertTrue(manager.enable_otel)
    
    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        correlation_id = self.manager.generate_correlation_id()
        
        self.assertIsInstance(correlation_id, str)
        self.assertTrue(correlation_id.startswith("test-service-"))
        self.assertEqual(len(correlation_id), len("test-service-") + 12)
        
        # Test uniqueness
        correlation_id2 = self.manager.generate_correlation_id()
        self.assertNotEqual(correlation_id, correlation_id2)
    
    def test_start_span(self):
        """Test starting a span"""
        correlation_id = self.manager.start_span("test_operation")
        
        self.assertIsInstance(correlation_id, str)
        self.assertTrue(correlation_id.startswith("test-service-"))
        self.assertIn(correlation_id, self.manager.active_traces)
        
        trace_context = self.manager.get_trace_context(correlation_id)
        self.assertIsNotNone(trace_context)
        self.assertEqual(trace_context.operation_name, "test_operation")
        self.assertEqual(trace_context.correlation_id, correlation_id)
        self.assertIsNotNone(trace_context.span_id)
        self.assertIsNone(trace_context.parent_span_id)
        
        # Check thread-local storage
        current_id = self.manager.get_current_correlation_id()
        self.assertEqual(current_id, correlation_id)
    
    def test_start_child_span(self):
        """Test starting a child span"""
        parent_id = self.manager.start_span("parent_operation")
        child_id = self.manager.start_child_span("child_operation")
        
        parent_context = self.manager.get_trace_context(parent_id)
        child_context = self.manager.get_trace_context(child_id)
        
        self.assertIsNotNone(parent_context)
        self.assertIsNotNone(child_context)
        
        # Child should have same trace_id as parent
        self.assertEqual(child_context.trace_id, parent_context.trace_id)
        self.assertEqual(child_context.parent_span_id, parent_context.span_id)
        self.assertEqual(child_context.operation_name, "child_operation")
    
    def test_end_span(self):
        """Test ending a span"""
        correlation_id = self.manager.start_span("test_operation")
        
        # Span should not be finished initially
        trace_context = self.manager.get_trace_context(correlation_id)
        self.assertFalse(trace_context.is_finished)
        
        # End the span
        self.manager.end_span(correlation_id, success=True)
        
        # Span should now be finished
        trace_context = self.manager.get_trace_context(correlation_id)
        self.assertTrue(trace_context.is_finished)
        self.assertTrue(trace_context.success)
        self.assertIsNotNone(trace_context.end_time)
        self.assertIsNotNone(trace_context.duration_ms)
    
    def test_end_span_with_failure(self):
        """Test ending a span with failure"""
        correlation_id = self.manager.start_span("test_operation")
        self.manager.end_span(correlation_id, success=False)
        
        trace_context = self.manager.get_trace_context(correlation_id)
        self.assertTrue(trace_context.is_finished)
        self.assertFalse(trace_context.success)
    
    def test_end_nonexistent_span(self):
        """Test ending a non-existent span"""
        # Should not raise an exception
        self.manager.end_span("nonexistent-id")
    
    def test_thread_local_storage(self):
        """Test thread-local storage behavior"""
        correlation_id = self.manager.start_span("test_operation")
        
        # Should be set in current thread
        current_id = self.manager.get_current_correlation_id()
        self.assertEqual(current_id, correlation_id)
        
        # Test setting manually
        self.manager.set_current_correlation_id("manual-id")
        current_id = self.manager.get_current_correlation_id()
        self.assertEqual(current_id, "manual-id")
        
        # Test clearing
        self.manager._clear_current_correlation_id()
        current_id = self.manager.get_current_correlation_id()
        self.assertIsNone(current_id)
    
    def test_thread_local_isolation(self):
        """Test thread-local storage isolation between threads"""
        results = {}
        
        def thread_function(thread_id):
            correlation_id = self.manager.start_span(f"operation_{thread_id}")
            results[thread_id] = self.manager.get_current_correlation_id()
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=thread_function, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Each thread should have its own correlation ID
        self.assertEqual(len(results), 3)
        correlation_ids = list(results.values())
        self.assertEqual(len(set(correlation_ids)), 3)  # All unique
    
    def test_propagate_context_from_headers(self):
        """Test propagating context from HTTP headers"""
        headers = {"X-Correlation-ID": "external-12345678"}
        
        correlation_id = self.manager.propagate_context_from_headers(headers)
        
        self.assertEqual(correlation_id, "external-12345678")
        
        # Should be set in thread-local storage
        current_id = self.manager.get_current_correlation_id()
        self.assertEqual(current_id, "external-12345678")
    
    def test_propagate_context_from_w3c_headers(self):
        """Test propagating context from W3C headers with OpenTelemetry enabled"""
        manager = TracingManager("test-service", enable_opentelemetry=True)
        
        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        
        correlation_id = manager.propagate_context_from_headers(headers)
        
        self.assertEqual(correlation_id, "0af7651916cd43dd8448eb211c80319c")
        
        # Should create trace context with W3C data
        trace_context = manager.get_trace_context(correlation_id)
        self.assertIsNotNone(trace_context)
        self.assertEqual(trace_context.trace_id, "0af7651916cd43dd8448eb211c80319c")
        self.assertEqual(trace_context.span_id, "b7ad6b7169203331")
    
    def test_inject_context_to_headers(self):
        """Test injecting context to HTTP headers"""
        correlation_id = self.manager.start_span("test_operation")
        headers = {}
        
        self.manager.inject_context_to_headers(correlation_id, headers)
        
        self.assertEqual(headers["X-Correlation-ID"], correlation_id)
        self.assertEqual(headers["X-Trace-ID"], correlation_id)
    
    def test_inject_context_to_headers_with_opentelemetry(self):
        """Test injecting context with OpenTelemetry enabled"""
        manager = TracingManager("test-service", enable_opentelemetry=True)
        correlation_id = manager.start_span("test_operation")
        headers = {}
        
        manager.inject_context_to_headers(correlation_id, headers)
        
        self.assertEqual(headers["X-Correlation-ID"], correlation_id)
        self.assertEqual(headers["X-Trace-ID"], correlation_id)
        self.assertIn("traceparent", headers)
        
        # Validate traceparent format
        traceparent = headers["traceparent"]
        self.assertTrue(traceparent.startswith("00-"))
        parts = traceparent.split("-")
        self.assertEqual(len(parts), 4)
    
    def test_cleanup_finished_traces(self):
        """Test cleaning up old finished traces"""
        # Create some traces
        correlation_id1 = self.manager.start_span("operation1")
        correlation_id2 = self.manager.start_span("operation2")
        
        # End one trace
        self.manager.end_span(correlation_id1)
        
        # Mock time to make trace appear old
        with patch('time.time', return_value=time.time() + 3700):  # 1 hour + 100 seconds
            self.manager.cleanup_finished_traces(max_age_seconds=3600)  # 1 hour
        
        # Old finished trace should be removed
        self.assertNotIn(correlation_id1, self.manager.active_traces)
        # Active trace should remain
        self.assertIn(correlation_id2, self.manager.active_traces)
    
    def test_get_nonexistent_trace_context(self):
        """Test getting non-existent trace context"""
        trace_context = self.manager.get_trace_context("nonexistent-id")
        self.assertIsNone(trace_context)


class TestTracingIntegratedLogger(unittest.TestCase):
    """Test TracingIntegratedLogger functionality"""
    
    def setUp(self):
        self.logger = TracingIntegratedLogger(
            service_name="test-service",
            namespace="test-namespace",
            enable_tracing=True,
            enable_performance_monitoring=False,
            enable_kubernetes_metadata=False,
            enable_sampling=False,
            enable_security_logging=False
        )
    
    def test_initialization(self):
        """Test logger initialization"""
        self.assertEqual(self.logger.service_name, "test-service")
        self.assertEqual(self.logger.namespace, "test-namespace")
        self.assertTrue(self.logger.enable_tracing)
        self.assertIsNotNone(self.logger._tracing_manager)
    
    def test_start_trace(self):
        """Test starting a trace through logger"""
        correlation_id = self.logger.start_trace("test_operation")
        
        self.assertIsInstance(correlation_id, str)
        self.assertTrue(correlation_id.startswith("test-service-"))
        
        # Should be available in tracing manager
        trace_context = self.logger._tracing_manager.get_trace_context(correlation_id)
        self.assertIsNotNone(trace_context)
        self.assertEqual(trace_context.operation_name, "test_operation")
    
    def test_end_trace(self):
        """Test ending a trace through logger"""
        correlation_id = self.logger.start_trace("test_operation")
        self.logger.end_trace(correlation_id, success=True)
        
        trace_context = self.logger._tracing_manager.get_trace_context(correlation_id)
        self.assertTrue(trace_context.is_finished)
        self.assertTrue(trace_context.success)
    
    def test_start_child_trace(self):
        """Test starting a child trace"""
        parent_id = self.logger.start_trace("parent_operation")
        child_id = self.logger.start_child_trace("child_operation", parent_id)
        
        parent_context = self.logger._tracing_manager.get_trace_context(parent_id)
        child_context = self.logger._tracing_manager.get_trace_context(child_id)
        
        self.assertEqual(child_context.trace_id, parent_context.trace_id)
        self.assertEqual(child_context.parent_span_id, parent_context.span_id)
    
    def test_logging_with_correlation_id(self):
        """Test logging with explicit correlation ID"""
        correlation_id = self.logger.start_trace("test_operation")
        
        # Capture stdout to verify log output
        with patch('builtins.print') as mock_print:
            self.logger.info("Test message", correlation_id=correlation_id)
            
            # Verify print was called
            mock_print.assert_called_once()
            
            # Get the logged JSON
            logged_json = mock_print.call_args[0][0]
            self.assertIn(correlation_id, logged_json)
            self.assertIn("Test message", logged_json)
    
    def test_logging_with_automatic_correlation_id(self):
        """Test logging with automatic correlation ID from thread-local"""
        correlation_id = self.logger.start_trace("test_operation")
        
        # Should automatically use correlation ID from thread-local storage
        with patch('builtins.print') as mock_print:
            self.logger.info("Test message")
            
            logged_json = mock_print.call_args[0][0]
            self.assertIn(correlation_id, logged_json)
    
    def test_logging_without_tracing(self):
        """Test logging when tracing is disabled"""
        logger = TracingIntegratedLogger(
            service_name="test-service",
            enable_tracing=False
        )
        
        with patch('builtins.print') as mock_print:
            logger.info("Test message")
            
            logged_json = mock_print.call_args[0][0]
            self.assertIn("Test message", logged_json)
            # Should not contain correlation_id when tracing is disabled
            self.assertNotIn("correlation_id", logged_json)
    
    def test_extract_trace_from_headers(self):
        """Test extracting trace from HTTP headers"""
        headers = {"X-Correlation-ID": "external-12345678"}
        
        correlation_id = self.logger.extract_trace_from_headers(headers)
        
        self.assertEqual(correlation_id, "external-12345678")
        
        # Should be set as current correlation ID
        current_id = self.logger.get_current_correlation_id()
        self.assertEqual(current_id, "external-12345678")
    
    def test_inject_trace_to_headers(self):
        """Test injecting trace to HTTP headers"""
        correlation_id = self.logger.start_trace("test_operation")
        
        headers = self.logger.inject_trace_to_headers(correlation_id)
        
        self.assertEqual(headers["X-Correlation-ID"], correlation_id)
        self.assertEqual(headers["X-Trace-ID"], correlation_id)
    
    def test_inject_trace_to_existing_headers(self):
        """Test injecting trace to existing headers"""
        correlation_id = self.logger.start_trace("test_operation")
        existing_headers = {"Content-Type": "application/json"}
        
        result_headers = self.logger.inject_trace_to_headers(correlation_id, existing_headers)
        
        self.assertEqual(result_headers["Content-Type"], "application/json")
        self.assertEqual(result_headers["X-Correlation-ID"], correlation_id)
        self.assertIs(result_headers, existing_headers)  # Should modify in place
    
    def test_get_current_correlation_id(self):
        """Test getting current correlation ID"""
        # Initially should be None
        self.assertIsNone(self.logger.get_current_correlation_id())
        
        # After starting trace, should return correlation ID
        correlation_id = self.logger.start_trace("test_operation")
        current_id = self.logger.get_current_correlation_id()
        self.assertEqual(current_id, correlation_id)
    
    def test_set_current_correlation_id(self):
        """Test setting current correlation ID"""
        self.logger.set_current_correlation_id("manual-12345678")
        
        current_id = self.logger.get_current_correlation_id()
        self.assertEqual(current_id, "manual-12345678")
    
    def test_cleanup_old_traces(self):
        """Test cleaning up old traces"""
        correlation_id = self.logger.start_trace("test_operation")
        self.logger.end_trace(correlation_id)
        
        # Should not raise an exception
        self.logger.cleanup_old_traces(max_age_seconds=3600)
    
    def test_all_log_levels(self):
        """Test all log levels with tracing"""
        correlation_id = self.logger.start_trace("test_operation")
        
        with patch('builtins.print') as mock_print:
            self.logger.debug("Debug message", correlation_id=correlation_id)
            self.logger.info("Info message", correlation_id=correlation_id)
            self.logger.warning("Warning message", correlation_id=correlation_id)
            self.logger.error("Error message", correlation_id=correlation_id)
            self.logger.critical("Critical message", correlation_id=correlation_id)
            
            # Should have called print 5 times
            self.assertEqual(mock_print.call_count, 5)
            
            # Check that all calls contain the correlation ID
            for call in mock_print.call_args_list:
                logged_json = call[0][0]
                self.assertIn(correlation_id, logged_json)
    
    def test_enhanced_log_entry_creation(self):
        """Test enhanced log entry creation with tracing"""
        correlation_id = self.logger.start_trace("test_operation")
        
        # Create log entry (internal method)
        log_entry = self.logger._create_enhanced_log_entry(
            "INFO", "Test message", correlation_id
        )
        
        self.assertEqual(log_entry.level, "INFO")
        self.assertEqual(log_entry.message, "Test message")
        self.assertEqual(log_entry.service, "test-service")
        self.assertEqual(log_entry.namespace, "test-namespace")
        self.assertEqual(log_entry.correlation_id, correlation_id)
        
        # Should have trace information
        trace_context = self.logger._tracing_manager.get_trace_context(correlation_id)
        self.assertEqual(log_entry.trace_id, trace_context.trace_id)
        self.assertEqual(log_entry.span_id, trace_context.span_id)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestTraceContext))
    suite.addTest(unittest.makeSuite(TestTraceContextPropagator))
    suite.addTest(unittest.makeSuite(TestTracingManager))
    suite.addTest(unittest.makeSuite(TestTracingIntegratedLogger))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)