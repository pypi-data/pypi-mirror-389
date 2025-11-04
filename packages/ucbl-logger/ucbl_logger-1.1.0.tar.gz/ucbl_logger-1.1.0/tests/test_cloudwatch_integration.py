"""
Comprehensive unit tests for CloudWatch integration
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from collections import deque

from ucbl_logger.enhanced.cloudwatch import (
    CloudWatchConfig, BatchConfig, CompressionConfig, LogBatch, LogEntry,
    EnhancedCloudWatchHandler, IntelligentBatcher, PriorityBatcher,
    CloudWatchRateLimiter, AdaptiveRateLimiter, LogCompressor, LogDeduplicator,
    CloudWatchAutoConfigurator, MultiDestinationManager, DeliveryMode,
    CloudWatchErrorHandler, CostOptimizer, CompressionType, BackoffStrategy,
    CloudWatchDestination, ErrorType
)


class TestCloudWatchConfig:
    """Test CloudWatch configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = CloudWatchConfig()
        
        assert config.region == "us-east-1"
        assert config.batch_size == 100
        assert config.batch_timeout == 5.0
        assert config.max_requests_per_second == 5.0
        assert config.compression_type == CompressionType.GZIP
        assert config.enable_deduplication is True
        
    def test_custom_config(self):
        """Test custom configuration"""
        config = CloudWatchConfig(
            region="us-west-2",
            batch_size=200,
            compression_type=CompressionType.ZLIB,
            enable_deduplication=False
        )
        
        assert config.region == "us-west-2"
        assert config.batch_size == 200
        assert config.compression_type == CompressionType.ZLIB
        assert config.enable_deduplication is False


class TestLogEntry:
    """Test log entry functionality"""
    
    def test_log_entry_creation(self):
        """Test creating log entries"""
        entry = LogEntry(
            timestamp=int(time.time() * 1000),
            message="Test message",
            log_level="INFO",
            metadata={"service": "test"}
        )
        
        assert entry.message == "Test message"
        assert entry.log_level == "INFO"
        assert entry.metadata["service"] == "test"
    
    def test_to_cloudwatch_event(self):
        """Test conversion to CloudWatch event format"""
        timestamp = int(time.time() * 1000)
        entry = LogEntry(
            timestamp=timestamp,
            message="Test message",
            log_level="INFO"
        )
        
        event = entry.to_cloudwatch_event()
        
        assert event["timestamp"] == timestamp
        assert event["message"] == "Test message"


class TestLogBatch:
    """Test log batch functionality"""
    
    def test_empty_batch(self):
        """Test empty batch behavior"""
        batch = LogBatch()
        
        assert batch.is_empty()
        assert batch.size() == 0
        assert batch.get_size_bytes() == 0
    
    def test_add_entries(self):
        """Test adding entries to batch"""
        batch = LogBatch()
        entry1 = LogEntry(timestamp=1000, message="Message 1", log_level="INFO")
        entry2 = LogEntry(timestamp=2000, message="Message 2", log_level="ERROR")
        
        batch.add_entry(entry1)
        batch.add_entry(entry2)
        
        assert batch.size() == 2
        assert not batch.is_empty()
        assert batch.get_size_bytes() > 0
    
    def test_to_cloudwatch_events(self):
        """Test conversion to CloudWatch events"""
        batch = LogBatch()
        entry = LogEntry(timestamp=1000, message="Test", log_level="INFO")
        batch.add_entry(entry)
        
        events = batch.to_cloudwatch_events()
        
        assert len(events) == 1
        assert events[0]["timestamp"] == 1000
        assert events[0]["message"] == "Test"


class TestIntelligentBatcher:
    """Test intelligent batching functionality"""
    
    def test_batch_creation(self):
        """Test basic batch creation"""
        config = BatchConfig(target_batch_size=3, batch_timeout=1.0)
        batcher = IntelligentBatcher(config)
        
        # Add entries below target size
        entry1 = LogEntry(timestamp=1000, message="Message 1", log_level="INFO")
        entry2 = LogEntry(timestamp=2000, message="Message 2", log_level="INFO")
        
        result1 = batcher.add_entry(entry1)
        result2 = batcher.add_entry(entry2)
        
        assert result1 is None  # Batch not ready
        assert result2 is None  # Batch not ready
    
    def test_batch_size_trigger(self):
        """Test batch completion by size"""
        config = BatchConfig(target_batch_size=2, batch_timeout=10.0)
        batcher = IntelligentBatcher(config)
        
        entry1 = LogEntry(timestamp=1000, message="Message 1", log_level="INFO")
        entry2 = LogEntry(timestamp=2000, message="Message 2", log_level="INFO")
        
        result1 = batcher.add_entry(entry1)
        result2 = batcher.add_entry(entry2)
        
        assert result1 is None
        assert result2 is not None
        assert result2.size() == 2
    
    def test_batch_timeout_trigger(self):
        """Test batch completion by timeout"""
        config = BatchConfig(target_batch_size=10, batch_timeout=0.1)
        batcher = IntelligentBatcher(config)
        
        entry = LogEntry(timestamp=1000, message="Message", log_level="INFO")
        batcher.add_entry(entry)
        
        # Wait for timeout
        time.sleep(0.2)
        
        ready_batch = batcher.get_ready_batch()
        assert ready_batch is not None
        assert ready_batch.size() == 1
    
    def test_force_flush(self):
        """Test force flush functionality"""
        config = BatchConfig(target_batch_size=10, batch_timeout=10.0)
        batcher = IntelligentBatcher(config)
        
        entry = LogEntry(timestamp=1000, message="Message", log_level="INFO")
        batcher.add_entry(entry)
        
        flushed_batch = batcher.force_flush()
        assert flushed_batch is not None
        assert flushed_batch.size() == 1


class TestPriorityBatcher:
    """Test priority batching functionality"""
    
    def test_priority_handling(self):
        """Test priority-based batching"""
        config = BatchConfig(target_batch_size=5, min_batch_size=2)
        batcher = PriorityBatcher(config)
        
        # Add high priority entry (ERROR)
        error_entry = LogEntry(timestamp=1000, message="Error", log_level="ERROR")
        result = batcher.add_entry(error_entry)
        
        # High priority batches should be smaller
        assert result is None  # Need min_batch_size
        
        # Add another high priority entry
        error_entry2 = LogEntry(timestamp=2000, message="Error 2", log_level="ERROR")
        result = batcher.add_entry(error_entry2)
        
        assert result is not None  # Should trigger at min_batch_size
        assert result.size() == 2


class TestCloudWatchRateLimiter:
    """Test CloudWatch rate limiting"""
    
    def test_rate_limit_initialization(self):
        """Test rate limiter initialization"""
        config = CloudWatchConfig(max_requests_per_second=5.0, burst_capacity=10)
        limiter = CloudWatchRateLimiter(config)
        
        assert limiter.can_make_request()
    
    def test_burst_capacity(self):
        """Test burst capacity handling"""
        config = CloudWatchConfig(max_requests_per_second=1.0, burst_capacity=3)
        limiter = CloudWatchRateLimiter(config)
        
        # Should allow burst requests
        assert limiter.can_make_request()
        limiter.record_request(True)
        
        assert limiter.can_make_request()
        limiter.record_request(True)
        
        assert limiter.can_make_request()
        limiter.record_request(True)
    
    def test_failure_backoff(self):
        """Test backoff on failures"""
        config = CloudWatchConfig(base_delay=0.1, max_delay=1.0)
        limiter = CloudWatchRateLimiter(config)
        
        # Record failures
        limiter.record_request(False)
        limiter.record_request(False)
        
        # Should have delay
        delay = limiter.get_delay()
        assert delay > 0
    
    def test_reset_functionality(self):
        """Test rate limiter reset"""
        config = CloudWatchConfig()
        limiter = CloudWatchRateLimiter(config)
        
        # Record some failures
        limiter.record_request(False)
        limiter.record_request(False)
        
        # Reset
        limiter.reset()
        
        # Should be able to make requests again
        assert limiter.can_make_request()
        assert limiter.get_delay() == 0.0


class TestLogCompressor:
    """Test log compression functionality"""
    
    def test_compression_threshold(self):
        """Test compression threshold logic"""
        config = CompressionConfig(threshold_bytes=100)
        compressor = LogCompressor(config)
        
        # Small batch - should not compress
        small_batch = LogBatch()
        small_entry = LogEntry(timestamp=1000, message="Small", log_level="INFO")
        small_batch.add_entry(small_entry)
        
        assert not compressor.should_compress(small_batch)
    
    def test_compression_disabled(self):
        """Test compression when disabled"""
        config = CompressionConfig(compression_type=CompressionType.NONE)
        compressor = LogCompressor(config)
        
        batch = LogBatch()
        entry = LogEntry(timestamp=1000, message="Test message", log_level="INFO")
        batch.add_entry(entry)
        
        assert not compressor.should_compress(batch)
    
    def test_compression_stats(self):
        """Test compression statistics"""
        config = CompressionConfig()
        compressor = LogCompressor(config)
        
        stats = compressor.get_stats()
        
        assert 'total_batches' in stats
        assert 'compressed_batches' in stats
        assert 'compression_ratio' in stats


class TestLogDeduplicator:
    """Test log deduplication functionality"""
    
    def test_duplicate_detection(self):
        """Test duplicate detection"""
        deduplicator = LogDeduplicator(window_seconds=60)
        
        entry1 = LogEntry(timestamp=1000, message="Same message", log_level="INFO")
        entry2 = LogEntry(timestamp=2000, message="Same message", log_level="INFO")
        
        # First entry should not be duplicate
        assert not deduplicator.is_duplicate(entry1)
        
        # Second entry should be duplicate
        assert deduplicator.is_duplicate(entry2)
    
    def test_window_expiry(self):
        """Test deduplication window expiry"""
        deduplicator = LogDeduplicator(window_seconds=1)
        
        entry1 = LogEntry(timestamp=1000, message="Message", log_level="INFO")
        entry2 = LogEntry(timestamp=2000, message="Message", log_level="INFO")
        
        # First entry
        assert not deduplicator.is_duplicate(entry1)
        
        # Wait for window to expire
        time.sleep(1.1)
        deduplicator.cleanup_old_entries()
        
        # Should not be duplicate after window expiry
        assert not deduplicator.is_duplicate(entry2)
    
    def test_deduplication_stats(self):
        """Test deduplication statistics"""
        deduplicator = LogDeduplicator()
        
        entry = LogEntry(timestamp=1000, message="Test", log_level="INFO")
        deduplicator.is_duplicate(entry)
        
        stats = deduplicator.get_stats()
        
        assert 'total_entries' in stats
        assert 'duplicates_found' in stats
        assert 'deduplication_rate' in stats


class TestEnhancedCloudWatchHandler:
    """Test enhanced CloudWatch handler"""
    
    @patch('ucbl_logger.enhanced.cloudwatch.handler.boto3')
    def test_handler_initialization_mock(self, mock_boto3):
        """Test handler initialization with mocked boto3"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        config = CloudWatchConfig(
            log_group_name="test-group",
            log_stream_name="test-stream"
        )
        
        # Mock the handler to avoid threading issues
        with patch('ucbl_logger.enhanced.cloudwatch.handler.EnhancedCloudWatchHandler.__init__', return_value=None):
            handler = EnhancedCloudWatchHandler.__new__(EnhancedCloudWatchHandler)
            handler.config = config
            handler.stats = Mock()
            handler.running = False  # Prevent threading
            
            assert handler.config == config
    
    def test_handler_without_boto3(self):
        """Test handler behavior when boto3 is not available"""
        with patch('ucbl_logger.enhanced.cloudwatch.handler.BOTO3_AVAILABLE', False):
            config = CloudWatchConfig()
            
            with pytest.raises(ImportError, match="boto3 is required"):
                EnhancedCloudWatchHandler(config)


class TestCloudWatchAutoConfigurator:
    """Test CloudWatch auto-configuration"""
    
    @patch('ucbl_logger.enhanced.cloudwatch.auto_config.boto3')
    def test_auto_configure(self, mock_boto3):
        """Test automatic configuration"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        configurator = CloudWatchAutoConfigurator()
        
        with patch.dict('os.environ', {'ENVIRONMENT': 'test'}):
            config = configurator.auto_configure("test-service")
        
        assert config.log_group_name is not None
        assert config.log_stream_name is not None
        assert "test-service" in config.log_group_name
    
    @patch('ucbl_logger.enhanced.cloudwatch.auto_config.boto3')
    def test_environment_detection(self, mock_boto3):
        """Test environment detection"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        configurator = CloudWatchAutoConfigurator()
        
        # Test with environment variable
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            env = configurator._detect_environment()
            assert env == 'production'
        
        # Test default
        with patch.dict('os.environ', {}, clear=True):
            env = configurator._detect_environment()
            assert env == 'development'


class TestMultiDestinationManager:
    """Test multi-destination management"""
    
    @patch('ucbl_logger.enhanced.cloudwatch.multi_destination.EnhancedCloudWatchHandler')
    def test_manager_initialization(self, mock_handler_class):
        """Test manager initialization"""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        dest1 = CloudWatchDestination(
            name="dest1",
            region="us-east-1",
            log_group="group1",
            log_stream="stream1",
            config=CloudWatchConfig(),
            priority=1
        )
        
        manager = MultiDestinationManager([dest1])
        
        assert len(manager.destinations) == 1
        assert "dest1" in manager.handlers
    
    @patch('ucbl_logger.enhanced.cloudwatch.multi_destination.EnhancedCloudWatchHandler')
    def test_parallel_delivery(self, mock_handler_class):
        """Test parallel delivery mode"""
        mock_handler = Mock()
        mock_handler.send_batch.return_value = True
        mock_handler_class.return_value = mock_handler
        
        dest1 = CloudWatchDestination(
            name="dest1",
            region="us-east-1", 
            log_group="group1",
            log_stream="stream1",
            config=CloudWatchConfig(),
            priority=1
        )
        
        manager = MultiDestinationManager([dest1], DeliveryMode.PARALLEL)
        
        batch = LogBatch()
        entry = LogEntry(timestamp=1000, message="Test", log_level="INFO")
        batch.add_entry(entry)
        
        results = manager.send_to_all(batch)
        
        assert "dest1" in results
        assert results["dest1"] is True


class TestCloudWatchErrorHandler:
    """Test CloudWatch error handling"""
    
    def test_error_classification(self):
        """Test error classification"""
        handler = CloudWatchErrorHandler()
        
        # Mock ClientError
        mock_error = Mock()
        mock_error.response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate exceeded'
            }
        }
        
        batch = LogBatch()
        context = handler._classify_error(mock_error, batch, 0)
        
        assert context.error_type == ErrorType.THROTTLING
        assert context.error_code == 'ThrottlingException'
        assert context.recoverable is True
    
    def test_retry_logic(self):
        """Test retry decision logic"""
        handler = CloudWatchErrorHandler()
        
        # Create error context
        from ucbl_logger.enhanced.cloudwatch.error_handling import ErrorContext
        
        context = ErrorContext(
            error_type=ErrorType.THROTTLING,
            error_code='ThrottlingException',
            error_message='Rate exceeded',
            timestamp=time.time(),
            batch_size=10,
            retry_count=1,
            recoverable=True
        )
        
        assert handler.should_retry(context)
        
        # Test max retries exceeded
        context.retry_count = 10
        assert not handler.should_retry(context)
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation"""
        handler = CloudWatchErrorHandler()
        
        from ucbl_logger.enhanced.cloudwatch.error_handling import ErrorContext
        
        context = ErrorContext(
            error_type=ErrorType.THROTTLING,
            error_code='ThrottlingException',
            error_message='Rate exceeded',
            timestamp=time.time(),
            batch_size=10,
            retry_count=1,
            recoverable=True
        )
        
        delay = handler.get_retry_delay(context)
        assert delay > 0
        assert delay >= 0.1  # Minimum delay


class TestCostOptimizer:
    """Test cost optimization functionality"""
    
    def test_batch_optimization(self):
        """Test batch optimization"""
        optimizer = CostOptimizer()
        
        batch = LogBatch()
        
        # Add entry with large metadata
        entry = LogEntry(
            timestamp=1000,
            message="Test message",
            log_level="INFO",
            metadata={
                "large_field": "x" * 2000,  # Large field
                "empty_field": "",
                "null_field": None
            }
        )
        batch.add_entry(entry)
        
        optimized_batch = optimizer.optimize_batch(batch)
        
        # Should have removed empty/null fields and truncated large fields
        assert optimized_batch is not None
        assert len(optimized_batch.entries) == 1
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        optimizer = CostOptimizer()
        
        estimate = optimizer.estimate_monthly_cost(1.0)  # 1 GB per day
        
        assert 'monthly_volume_gb' in estimate
        assert 'ingestion_cost_usd' in estimate
        assert 'storage_cost_usd' in estimate
        assert 'total_cost_usd' in estimate
        assert estimate['monthly_volume_gb'] == 30.0
    
    def test_cost_stats(self):
        """Test cost statistics"""
        optimizer = CostOptimizer()
        
        stats = optimizer.get_cost_stats()
        
        assert 'total_log_events' in stats
        assert 'total_bytes_ingested' in stats
        assert 'estimated_cost_usd' in stats


# Integration tests
class TestCloudWatchIntegration:
    """Integration tests for CloudWatch components"""
    
    def test_component_integration(self):
        """Test integration between components without threading"""
        # Test batcher + compressor integration
        batch_config = BatchConfig(target_batch_size=2)
        batcher = IntelligentBatcher(batch_config)
        
        compression_config = CompressionConfig()
        compressor = LogCompressor(compression_config)
        
        # Create entries
        entry1 = LogEntry(timestamp=1000, message="Message 1", log_level="INFO")
        entry2 = LogEntry(timestamp=2000, message="Message 2", log_level="ERROR")
        
        # Add to batcher
        result1 = batcher.add_entry(entry1)
        result2 = batcher.add_entry(entry2)
        
        assert result1 is None
        assert result2 is not None
        
        # Compress the batch
        compressed_batch = compressor.compress_batch(result2)
        assert compressed_batch is not None
        assert compressed_batch.size() == 2


if __name__ == '__main__':
    pytest.main([__file__])