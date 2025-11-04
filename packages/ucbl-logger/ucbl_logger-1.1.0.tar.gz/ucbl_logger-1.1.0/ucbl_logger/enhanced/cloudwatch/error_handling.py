"""
CloudWatch Error Handling and Retry Logic

Specialized error handling, retry logic, and cost optimization for CloudWatch.
"""

import time
import logging
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import deque

try:
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception
    BotoCoreError = Exception

from .models import LogBatch, LogEntry


class ErrorType(Enum):
    """Types of CloudWatch errors."""
    THROTTLING = "throttling"
    RATE_LIMIT = "rate_limit"
    SEQUENCE_TOKEN = "sequence_token"
    RESOURCE_NOT_FOUND = "resource_not_found"
    INVALID_PARAMETER = "invalid_parameter"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error."""
    error_type: ErrorType
    error_code: str
    error_message: str
    timestamp: float
    batch_size: int
    retry_count: int = 0
    recoverable: bool = True


class CloudWatchErrorHandler:
    """Handles CloudWatch-specific errors with intelligent retry logic."""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)
        self.sequence_tokens: Dict[str, str] = {}  # log_stream -> token
        
        # Error classification mapping
        self.error_mapping = {
            'ThrottlingException': ErrorType.THROTTLING,
            'DataAlreadyAcceptedException': ErrorType.SEQUENCE_TOKEN,
            'InvalidSequenceTokenException': ErrorType.SEQUENCE_TOKEN,
            'ResourceNotFoundException': ErrorType.RESOURCE_NOT_FOUND,
            'InvalidParameterException': ErrorType.INVALID_PARAMETER,
            'ServiceUnavailableException': ErrorType.SERVICE_UNAVAILABLE,
        }
        
        # Retry configuration by error type
        self.retry_config = {
            ErrorType.THROTTLING: {'max_retries': 5, 'base_delay': 2.0, 'max_delay': 60.0},
            ErrorType.SEQUENCE_TOKEN: {'max_retries': 3, 'base_delay': 0.5, 'max_delay': 5.0},
            ErrorType.SERVICE_UNAVAILABLE: {'max_retries': 4, 'base_delay': 1.0, 'max_delay': 30.0},
            ErrorType.NETWORK_ERROR: {'max_retries': 3, 'base_delay': 1.0, 'max_delay': 15.0},
            ErrorType.RESOURCE_NOT_FOUND: {'max_retries': 1, 'base_delay': 1.0, 'max_delay': 5.0},
            ErrorType.INVALID_PARAMETER: {'max_retries': 0, 'base_delay': 0.0, 'max_delay': 0.0},
        }
    
    def handle_error(self, 
                    error: Exception, 
                    batch: LogBatch,
                    log_group: str,
                    log_stream: str,
                    retry_count: int = 0) -> ErrorContext:
        """Handle and classify an error."""
        
        error_context = self._classify_error(error, batch, retry_count)
        
        # Record error in history
        self.error_history.append(error_context)
        
        # Handle specific error types
        if error_context.error_type == ErrorType.SEQUENCE_TOKEN:
            self._handle_sequence_token_error(error, log_group, log_stream)
        elif error_context.error_type == ErrorType.RESOURCE_NOT_FOUND:
            self._handle_resource_not_found_error(error, log_group, log_stream)
        
        return error_context
    
    def should_retry(self, error_context: ErrorContext) -> bool:
        """Determine if an error should be retried."""
        if not error_context.recoverable:
            return False
        
        config = self.retry_config.get(error_context.error_type, {'max_retries': 0})
        return error_context.retry_count < config['max_retries']
    
    def get_retry_delay(self, error_context: ErrorContext) -> float:
        """Calculate retry delay for an error."""
        config = self.retry_config.get(error_context.error_type, {'base_delay': 1.0, 'max_delay': 60.0})
        
        base_delay = config['base_delay']
        max_delay = config['max_delay']
        
        # Exponential backoff with jitter
        delay = min(base_delay * (2 ** error_context.retry_count), max_delay)
        
        # Add jitter (±25%)
        jitter = delay * 0.25 * (random.random() - 0.5)
        delay += jitter
        
        # Apply additional delay based on recent error rate
        error_rate_multiplier = self._get_error_rate_multiplier(error_context.error_type)
        delay *= error_rate_multiplier
        
        return max(0.1, delay)  # Minimum 100ms delay
    
    def get_sequence_token(self, log_stream: str) -> Optional[str]:
        """Get the current sequence token for a log stream."""
        return self.sequence_tokens.get(log_stream)
    
    def update_sequence_token(self, log_stream: str, token: str) -> None:
        """Update the sequence token for a log stream."""
        self.sequence_tokens[log_stream] = token
    
    def _classify_error(self, error: Exception, batch: LogBatch, retry_count: int) -> ErrorContext:
        """Classify an error and create context."""
        
        error_type = ErrorType.UNKNOWN
        error_code = "Unknown"
        error_message = str(error)
        recoverable = True
        
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', 'Unknown')
            error_message = error.response.get('Error', {}).get('Message', str(error))
            error_type = self.error_mapping.get(error_code, ErrorType.UNKNOWN)
            
            # Some errors are not recoverable
            if error_code in ['InvalidParameterException', 'AccessDeniedException']:
                recoverable = False
                
        elif isinstance(error, BotoCoreError):
            error_type = ErrorType.NETWORK_ERROR
            error_message = str(error)
            
        return ErrorContext(
            error_type=error_type,
            error_code=error_code,
            error_message=error_message,
            timestamp=time.time(),
            batch_size=batch.size(),
            retry_count=retry_count,
            recoverable=recoverable
        )
    
    def _handle_sequence_token_error(self, error: Exception, log_group: str, log_stream: str) -> None:
        """Handle sequence token errors by extracting the expected token."""
        if not isinstance(error, ClientError):
            return
        
        error_message = error.response.get('Error', {}).get('Message', '')
        
        # Try to extract expected sequence token from error message
        # Format: "The given sequenceToken is invalid. The next expected sequenceToken is: 12345"
        import re
        
        token_match = re.search(r'sequenceToken is: (\d+)', error_message)
        if token_match:
            expected_token = token_match.group(1)
            self.update_sequence_token(log_stream, expected_token)
            logging.info(f"Updated sequence token for {log_stream}: {expected_token}")
        else:
            # If we can't extract the token, clear it to force a refresh
            if log_stream in self.sequence_tokens:
                del self.sequence_tokens[log_stream]
    
    def _handle_resource_not_found_error(self, error: Exception, log_group: str, log_stream: str) -> None:
        """Handle resource not found errors."""
        if isinstance(error, ClientError):
            error_message = error.response.get('Error', {}).get('Message', '')
            logging.warning(f"Resource not found: {error_message}")
            
            # Clear sequence token for this stream
            if log_stream in self.sequence_tokens:
                del self.sequence_tokens[log_stream]
    
    def _get_error_rate_multiplier(self, error_type: ErrorType) -> float:
        """Get error rate multiplier for delay calculation."""
        # Count recent errors of this type
        current_time = time.time()
        recent_errors = [
            err for err in self.error_history
            if err.error_type == error_type and current_time - err.timestamp < 300  # 5 minutes
        ]
        
        if len(recent_errors) < 5:
            return 1.0
        
        # Increase delay based on error frequency
        error_rate = len(recent_errors) / 300.0  # errors per second
        
        if error_rate > 0.1:  # More than 1 error per 10 seconds
            return 2.0
        elif error_rate > 0.05:  # More than 1 error per 20 seconds
            return 1.5
        else:
            return 1.0
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        current_time = time.time()
        
        # Recent errors (last hour)
        recent_errors = [
            err for err in self.error_history
            if current_time - err.timestamp < 3600
        ]
        
        # Count by error type
        error_counts = {}
        for error in recent_errors:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Calculate error rates
        total_errors = len(recent_errors)
        error_rates = {}
        if total_errors > 0:
            for error_type, count in error_counts.items():
                error_rates[error_type] = count / total_errors
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': total_errors,
            'error_counts': error_counts,
            'error_rates': error_rates,
            'sequence_tokens_cached': len(self.sequence_tokens)
        }


class CostOptimizer:
    """Optimizes CloudWatch costs through various strategies."""
    
    def __init__(self):
        self.cost_stats = {
            'total_log_events': 0,
            'total_bytes_ingested': 0,
            'compressed_bytes_saved': 0,
            'deduplicated_events': 0,
            'estimated_cost_usd': 0.0
        }
        
        # CloudWatch pricing (approximate, varies by region)
        self.pricing = {
            'ingestion_per_gb': 0.50,  # USD per GB ingested
            'storage_per_gb_month': 0.03,  # USD per GB stored per month
        }
    
    def optimize_batch(self, batch: LogBatch) -> LogBatch:
        """Apply cost optimization strategies to a batch."""
        
        # Record original size
        original_size = batch.get_size_bytes()
        
        # Apply optimizations
        optimized_batch = self._remove_redundant_fields(batch)
        optimized_batch = self._truncate_large_messages(optimized_batch)
        
        # Update cost stats
        final_size = optimized_batch.get_size_bytes()
        bytes_saved = original_size - final_size
        
        self.cost_stats['total_log_events'] += batch.size()
        self.cost_stats['total_bytes_ingested'] += final_size
        
        if bytes_saved > 0:
            self.cost_stats['compressed_bytes_saved'] += bytes_saved
        
        # Estimate cost
        gb_ingested = final_size / (1024 ** 3)
        cost = gb_ingested * self.pricing['ingestion_per_gb']
        self.cost_stats['estimated_cost_usd'] += cost
        
        return optimized_batch
    
    def _remove_redundant_fields(self, batch: LogBatch) -> LogBatch:
        """Remove redundant or unnecessary fields from log entries."""
        
        for entry in batch.entries:
            # Remove empty metadata fields
            if hasattr(entry, 'metadata') and entry.metadata:
                entry.metadata = {k: v for k, v in entry.metadata.items() if v is not None and v != ''}
            
            # Truncate very long field values
            if hasattr(entry, 'metadata') and entry.metadata:
                for key, value in entry.metadata.items():
                    if isinstance(value, str) and len(value) > 1000:
                        entry.metadata[key] = value[:997] + '...'
        
        return batch
    
    def _truncate_large_messages(self, batch: LogBatch, max_message_size: int = 8192) -> LogBatch:
        """Truncate messages that are too large."""
        
        for entry in batch.entries:
            if len(entry.message) > max_message_size:
                entry.message = entry.message[:max_message_size - 3] + '...'
        
        return batch
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """Get cost optimization statistics."""
        stats = self.cost_stats.copy()
        
        # Calculate additional metrics
        if stats['total_log_events'] > 0:
            stats['avg_bytes_per_event'] = stats['total_bytes_ingested'] / stats['total_log_events']
        
        if stats['total_bytes_ingested'] > 0:
            stats['compression_ratio'] = stats['compressed_bytes_saved'] / (stats['total_bytes_ingested'] + stats['compressed_bytes_saved'])
        
        # Estimate monthly storage cost (assuming 30-day retention)
        gb_stored = stats['total_bytes_ingested'] / (1024 ** 3)
        stats['estimated_monthly_storage_cost_usd'] = gb_stored * self.pricing['storage_per_gb_month']
        
        return stats
    
    def estimate_monthly_cost(self, daily_log_volume_gb: float) -> Dict[str, float]:
        """Estimate monthly CloudWatch costs."""
        
        monthly_volume_gb = daily_log_volume_gb * 30
        
        ingestion_cost = monthly_volume_gb * self.pricing['ingestion_per_gb']
        storage_cost = monthly_volume_gb * self.pricing['storage_per_gb_month']
        
        return {
            'monthly_volume_gb': monthly_volume_gb,
            'ingestion_cost_usd': ingestion_cost,
            'storage_cost_usd': storage_cost,
            'total_cost_usd': ingestion_cost + storage_cost
        }