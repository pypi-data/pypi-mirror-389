"""
Enhanced CloudWatch Handler

Main CloudWatch handler with intelligent batching, rate limiting, and cost optimization.
"""

import time
import threading
import logging
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, Future
import json

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    BotoCoreError = Exception

from .interfaces import ICloudWatchHandler
from .models import (
    LogEntry, LogBatch, CloudWatchConfig, DeliveryStats, 
    CompressionType, CloudWatchDestination
)
from .batching import IntelligentBatcher, PriorityBatcher
from .rate_limiter import CloudWatchRateLimiter, AdaptiveRateLimiter
from .compression import LogCompressor, LogDeduplicator


class EnhancedCloudWatchHandler(ICloudWatchHandler):
    """Enhanced CloudWatch handler with intelligent batching and optimization."""
    
    def __init__(self, config: CloudWatchConfig):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for CloudWatch integration. Install with: pip install boto3")
        
        self.config = config
        self.stats = DeliveryStats()
        self.lock = threading.Lock()
        
        # Initialize CloudWatch client
        self.client = boto3.client('logs', region_name=config.region)
        
        # Initialize components
        from .batching import BatchConfig
        from .compression import CompressionConfig
        
        batch_config = BatchConfig(
            target_batch_size=config.batch_size,
            max_batch_size=config.max_batch_size,
            batch_timeout=config.batch_timeout
        )
        
        compression_config = CompressionConfig(
            compression_type=config.compression_type,
            threshold_bytes=config.compression_threshold
        )
        
        self.batcher = IntelligentBatcher(batch_config)
        self.rate_limiter = AdaptiveRateLimiter(config)
        self.compressor = LogCompressor(compression_config)
        
        if config.enable_deduplication:
            self.deduplicator = LogDeduplicator(config.deduplication_window)
        else:
            self.deduplicator = None
        
        # Background processing
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cloudwatch")
        self.running = True
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flush_thread.start()
        
        # Auto-create log group and stream if needed
        if config.auto_create_group or config.auto_create_stream:
            self._ensure_log_destination()
    
    def send_log(self, entry: LogEntry) -> bool:
        """Send a single log entry to CloudWatch."""
        if not self.running:
            return False
        
        # Check for duplicates
        if self.deduplicator and self.deduplicator.is_duplicate(entry):
            return True  # Skip duplicate, but report success
        
        # Add to batcher
        ready_batch = self.batcher.add_entry(entry)
        
        if ready_batch:
            # Submit batch for async processing
            future = self.executor.submit(self._send_batch_internal, ready_batch)
            return True  # Return immediately for async processing
        
        return True
    
    def send_batch(self, batch: LogBatch) -> bool:
        """Send a batch of log entries to CloudWatch."""
        if not self.running:
            return False
        
        return self._send_batch_internal(batch)
    
    def flush(self) -> None:
        """Flush any pending log entries."""
        ready_batch = self.batcher.force_flush()
        if ready_batch:
            self._send_batch_internal(ready_batch)
    
    def get_stats(self) -> DeliveryStats:
        """Get delivery statistics."""
        with self.lock:
            return self.stats
    
    def is_healthy(self) -> bool:
        """Check if the handler is healthy."""
        with self.lock:
            # Consider healthy if failure rate is low
            if self.stats.total_batches_sent == 0:
                return True
            
            failure_rate = self.stats.total_failures / (self.stats.total_batches_sent + self.stats.total_failures)
            return failure_rate < 0.1  # Less than 10% failure rate
    
    def shutdown(self) -> None:
        """Shutdown the handler gracefully."""
        self.running = False
        
        # Flush any remaining logs
        self.flush()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
    
    def _send_batch_internal(self, batch: LogBatch) -> bool:
        """Internal method to send batch to CloudWatch."""
        try:
            # Wait for rate limiter
            while not self.rate_limiter.can_make_request():
                delay = self.rate_limiter.get_delay()
                if delay > 0:
                    time.sleep(min(delay, 1.0))  # Max 1 second wait
            
            # Compress batch if beneficial
            compressed_batch = self.compressor.compress_batch(batch)
            
            # Convert to CloudWatch format
            log_events = compressed_batch.to_cloudwatch_events()
            
            # Sort events by timestamp (CloudWatch requirement)
            log_events.sort(key=lambda x: x['timestamp'])
            
            # Send to CloudWatch
            response = self.client.put_log_events(
                logGroupName=self.config.log_group_name,
                logStreamName=self.config.log_stream_name,
                logEvents=log_events
            )
            
            # Record success
            self.rate_limiter.record_request(True)
            
            with self.lock:
                self.stats.update_delivery(compressed_batch, True)
            
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code == 'ThrottlingException':
                # Handle throttling
                self.rate_limiter.record_request(False)
                return False
            elif error_code in ['InvalidSequenceTokenException', 'DataAlreadyAcceptedException']:
                # Handle sequence token issues
                self._handle_sequence_token_error(e)
                return False
            else:
                # Other client errors
                logging.error(f"CloudWatch client error: {e}")
                self.rate_limiter.record_request(False)
                
                with self.lock:
                    self.stats.update_delivery(batch, False)
                
                return False
                
        except Exception as e:
            logging.error(f"Unexpected error sending to CloudWatch: {e}")
            self.rate_limiter.record_request(False)
            
            with self.lock:
                self.stats.update_delivery(batch, False)
            
            return False
    
    def _flush_worker(self) -> None:
        """Background worker to flush batches periodically."""
        while self.running:
            try:
                # Check for ready batches
                ready_batch = self.batcher.get_ready_batch()
                if ready_batch:
                    self._send_batch_internal(ready_batch)
                
                # Clean up deduplicator if enabled
                if self.deduplicator:
                    self.deduplicator.cleanup_old_entries()
                
                # Sleep for a short interval
                time.sleep(1.0)
                
            except Exception as e:
                logging.error(f"Error in flush worker: {e}")
                time.sleep(5.0)  # Longer sleep on error
    
    def _ensure_log_destination(self) -> None:
        """Ensure log group and stream exist."""
        try:
            # Create log group if needed
            if self.config.auto_create_group and self.config.log_group_name:
                try:
                    self.client.create_log_group(
                        logGroupName=self.config.log_group_name,
                        tags=self.config.default_tags
                    )
                except ClientError as e:
                    if e.response.get('Error', {}).get('Code') != 'ResourceAlreadyExistsException':
                        raise
            
            # Create log stream if needed
            if self.config.auto_create_stream and self.config.log_stream_name:
                try:
                    self.client.create_log_stream(
                        logGroupName=self.config.log_group_name,
                        logStreamName=self.config.log_stream_name
                    )
                except ClientError as e:
                    if e.response.get('Error', {}).get('Code') != 'ResourceAlreadyExistsException':
                        raise
                        
        except Exception as e:
            logging.warning(f"Could not ensure log destination: {e}")
    
    def _handle_sequence_token_error(self, error: ClientError) -> None:
        """Handle sequence token errors by refreshing the token."""
        try:
            # Get the expected sequence token from the error
            error_message = error.response.get('Error', {}).get('Message', '')
            
            # This is a simplified approach - in production, you'd want to
            # properly parse the expected sequence token from the error message
            # and retry with the correct token
            logging.warning(f"Sequence token error: {error_message}")
            
        except Exception as e:
            logging.error(f"Error handling sequence token: {e}")
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics from all components."""
        stats = {
            'delivery': self.get_stats().__dict__,
            'batching': self.batcher.get_stats(),
            'rate_limiting': self.rate_limiter.get_stats(),
            'compression': self.compressor.get_stats()
        }
        
        if self.deduplicator:
            stats['deduplication'] = self.deduplicator.get_stats()
        
        return stats


class MultiDestinationCloudWatchHandler(ICloudWatchHandler):
    """CloudWatch handler supporting multiple destinations with failover."""
    
    def __init__(self, destinations: List[CloudWatchDestination]):
        self.destinations = sorted(destinations, key=lambda d: d.priority)
        self.handlers: Dict[str, EnhancedCloudWatchHandler] = {}
        self.stats = DeliveryStats()
        self.lock = threading.Lock()
        
        # Initialize handlers for each destination
        for dest in self.destinations:
            if dest.enabled:
                self.handlers[dest.name] = EnhancedCloudWatchHandler(dest.config)
    
    def send_log(self, entry: LogEntry) -> bool:
        """Send log to all enabled destinations."""
        success_count = 0
        
        for dest in self.destinations:
            if not dest.enabled or dest.name not in self.handlers:
                continue
            
            try:
                if self.handlers[dest.name].send_log(entry):
                    success_count += 1
                else:
                    # If primary destination fails, try failover
                    if dest.priority == 1:  # Primary destination
                        self._try_failover_destinations(entry)
            except Exception as e:
                logging.error(f"Error sending to destination {dest.name}: {e}")
        
        return success_count > 0
    
    def send_batch(self, batch: LogBatch) -> bool:
        """Send batch to all destinations."""
        success_count = 0
        
        for dest in self.destinations:
            if not dest.enabled or dest.name not in self.handlers:
                continue
            
            try:
                if self.handlers[dest.name].send_batch(batch):
                    success_count += 1
            except Exception as e:
                logging.error(f"Error sending batch to destination {dest.name}: {e}")
        
        return success_count > 0
    
    def flush(self) -> None:
        """Flush all handlers."""
        for handler in self.handlers.values():
            try:
                handler.flush()
            except Exception as e:
                logging.error(f"Error flushing handler: {e}")
    
    def get_stats(self) -> DeliveryStats:
        """Get aggregated statistics."""
        with self.lock:
            # Aggregate stats from all handlers
            total_stats = DeliveryStats()
            
            for handler in self.handlers.values():
                handler_stats = handler.get_stats()
                total_stats.total_batches_sent += handler_stats.total_batches_sent
                total_stats.total_entries_sent += handler_stats.total_entries_sent
                total_stats.total_bytes_sent += handler_stats.total_bytes_sent
                total_stats.total_failures += handler_stats.total_failures
                total_stats.total_retries += handler_stats.total_retries
            
            return total_stats
    
    def is_healthy(self) -> bool:
        """Check if at least one handler is healthy."""
        for handler in self.handlers.values():
            if handler.is_healthy():
                return True
        return False
    
    def _try_failover_destinations(self, entry: LogEntry) -> bool:
        """Try sending to failover destinations."""
        for dest in self.destinations:
            if dest.priority > 1 and dest.enabled and dest.name in self.handlers:
                try:
                    if self.handlers[dest.name].send_log(entry):
                        return True
                except Exception as e:
                    logging.error(f"Failover destination {dest.name} failed: {e}")
        
        return False
    
    def shutdown(self) -> None:
        """Shutdown all handlers."""
        for handler in self.handlers.values():
            try:
                handler.shutdown()
            except Exception as e:
                logging.error(f"Error shutting down handler: {e}")