"""
Log Compression for CloudWatch

Implements log compression and deduplication to minimize CloudWatch costs.
"""

import gzip
import zlib
import json
import hashlib
import time
import threading
from typing import Dict, Set, Optional
from collections import defaultdict, deque

from .interfaces import ICompressor, IDeduplicator
from .models import LogBatch, LogEntry, CompressionType, CompressionConfig


class LogCompressor(ICompressor):
    """Compressor for CloudWatch log batches."""
    
    def __init__(self, config: CompressionConfig):
        self.config = config
        self.compression_stats = {
            'total_batches': 0,
            'compressed_batches': 0,
            'total_original_size': 0,
            'total_compressed_size': 0
        }
        self.lock = threading.Lock()
    
    def compress_batch(self, batch: LogBatch) -> LogBatch:
        """Compress a log batch if beneficial."""
        if not self.should_compress(batch):
            return batch
        
        # Convert batch to JSON string
        events = batch.to_cloudwatch_events()
        json_data = json.dumps(events, separators=(',', ':'))
        original_data = json_data.encode('utf-8')
        original_size = len(original_data)
        
        # Compress based on configuration
        if self.config.compression_type == CompressionType.GZIP:
            compressed_data = gzip.compress(
                original_data, 
                compresslevel=self.config.compression_level
            )
        elif self.config.compression_type == CompressionType.ZLIB:
            compressed_data = zlib.compress(
                original_data, 
                level=self.config.compression_level
            )
        else:
            # No compression
            return batch
        
        compressed_size = len(compressed_data)
        
        # Only use compression if it provides significant benefit
        if compressed_size < original_size * 0.9:  # At least 10% reduction
            batch.compressed = True
            batch.compressed_size = compressed_size
            batch.original_size = original_size
            
            # Update stats
            with self.lock:
                self.compression_stats['compressed_batches'] += 1
                self.compression_stats['total_compressed_size'] += compressed_size
        
        # Always update total stats
        with self.lock:
            self.compression_stats['total_batches'] += 1
            self.compression_stats['total_original_size'] += original_size
        
        return batch
    
    def should_compress(self, batch: LogBatch) -> bool:
        """Check if a batch should be compressed."""
        if self.config.compression_type == CompressionType.NONE:
            return False
        
        # Check size threshold
        batch_size = batch.get_size_bytes()
        return batch_size >= self.config.threshold_bytes
    
    def get_compression_ratio(self) -> float:
        """Get the average compression ratio."""
        with self.lock:
            if self.compression_stats['total_original_size'] == 0:
                return 1.0
            
            return (self.compression_stats['total_compressed_size'] / 
                   self.compression_stats['total_original_size'])
    
    def get_stats(self) -> dict:
        """Get compression statistics."""
        with self.lock:
            stats = self.compression_stats.copy()
            
            if stats['total_batches'] > 0:
                stats['compression_rate'] = stats['compressed_batches'] / stats['total_batches']
            else:
                stats['compression_rate'] = 0.0
            
            stats['compression_ratio'] = self.get_compression_ratio()
            
            return stats


class LogDeduplicator(IDeduplicator):
    """Deduplicator for CloudWatch logs."""
    
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self.seen_hashes: Dict[str, float] = {}  # hash -> timestamp
        self.message_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        # Track deduplication stats
        self.stats = {
            'total_entries': 0,
            'duplicates_found': 0,
            'unique_messages': 0
        }
    
    def is_duplicate(self, entry: LogEntry) -> bool:
        """Check if an entry is a duplicate."""
        with self.lock:
            self.stats['total_entries'] += 1
            
            # Create hash of message content
            message_hash = self._hash_entry(entry)
            current_time = time.time()
            
            # Clean up old entries first
            self._cleanup_old_entries_internal(current_time)
            
            # Check if we've seen this hash recently
            if message_hash in self.seen_hashes:
                last_seen = self.seen_hashes[message_hash]
                if current_time - last_seen < self.window_seconds:
                    self.stats['duplicates_found'] += 1
                    self.message_counts[message_hash] += 1
                    return True
            
            # Not a duplicate, record it
            self.seen_hashes[message_hash] = current_time
            self.message_counts[message_hash] = 1
            self.stats['unique_messages'] += 1
            return False
    
    def add_entry(self, entry: LogEntry) -> None:
        """Add an entry to the deduplication cache."""
        with self.lock:
            message_hash = self._hash_entry(entry)
            self.seen_hashes[message_hash] = time.time()
    
    def cleanup_old_entries(self) -> None:
        """Clean up old entries from the cache."""
        with self.lock:
            self._cleanup_old_entries_internal(time.time())
    
    def _cleanup_old_entries_internal(self, current_time: float) -> None:
        """Internal cleanup method (assumes lock is held)."""
        cutoff_time = current_time - self.window_seconds
        
        # Remove old entries
        old_hashes = [
            hash_key for hash_key, timestamp in self.seen_hashes.items()
            if timestamp < cutoff_time
        ]
        
        for hash_key in old_hashes:
            del self.seen_hashes[hash_key]
            if hash_key in self.message_counts:
                del self.message_counts[hash_key]
    
    def _hash_entry(self, entry: LogEntry) -> str:
        """Create a hash for an entry."""
        # Include message, log level, and some metadata for hashing
        hash_content = {
            'message': entry.message,
            'log_level': entry.log_level,
            # Include some metadata but not timestamp
            'service': entry.metadata.get('service', ''),
            'component': entry.metadata.get('component', '')
        }
        
        hash_string = json.dumps(hash_content, sort_keys=True)
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
    
    def get_stats(self) -> dict:
        """Get deduplication statistics."""
        with self.lock:
            stats = self.stats.copy()
            
            if stats['total_entries'] > 0:
                stats['deduplication_rate'] = stats['duplicates_found'] / stats['total_entries']
            else:
                stats['deduplication_rate'] = 0.0
            
            stats['cache_size'] = len(self.seen_hashes)
            stats['top_duplicates'] = dict(
                sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            
            return stats


class SmartDeduplicator(IDeduplicator):
    """Advanced deduplicator with pattern recognition."""
    
    def __init__(self, window_seconds: int = 300):
        self.base_deduplicator = LogDeduplicator(window_seconds)
        
        # Pattern tracking for smart deduplication
        self.pattern_cache: Dict[str, Dict] = {}
        self.pattern_stats = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def is_duplicate(self, entry: LogEntry) -> bool:
        """Check if entry is duplicate using pattern recognition."""
        # First check basic deduplication
        if self.base_deduplicator.is_duplicate(entry):
            return True
        
        # Check for pattern-based duplication
        return self._check_pattern_duplicate(entry)
    
    def add_entry(self, entry: LogEntry) -> None:
        """Add entry to both basic and pattern caches."""
        self.base_deduplicator.add_entry(entry)
        self._update_patterns(entry)
    
    def cleanup_old_entries(self) -> None:
        """Clean up old entries from all caches."""
        self.base_deduplicator.cleanup_old_entries()
        self._cleanup_patterns()
    
    def _check_pattern_duplicate(self, entry: LogEntry) -> bool:
        """Check for pattern-based duplicates."""
        with self.lock:
            # Extract patterns from message
            patterns = self._extract_patterns(entry.message)
            
            current_time = time.time()
            
            for pattern in patterns:
                if pattern in self.pattern_cache:
                    pattern_info = self.pattern_cache[pattern]
                    
                    # Check if pattern occurred recently
                    if current_time - pattern_info['last_seen'] < 60:  # 1 minute
                        # Check frequency
                        if pattern_info['count'] > 5:  # Seen more than 5 times
                            pattern_info['count'] += 1
                            pattern_info['last_seen'] = current_time
                            return True
            
            return False
    
    def _update_patterns(self, entry: LogEntry) -> None:
        """Update pattern tracking."""
        with self.lock:
            patterns = self._extract_patterns(entry.message)
            current_time = time.time()
            
            for pattern in patterns:
                if pattern not in self.pattern_cache:
                    self.pattern_cache[pattern] = {
                        'count': 1,
                        'first_seen': current_time,
                        'last_seen': current_time
                    }
                else:
                    self.pattern_cache[pattern]['count'] += 1
                    self.pattern_cache[pattern]['last_seen'] = current_time
    
    def _extract_patterns(self, message: str) -> Set[str]:
        """Extract patterns from log message."""
        patterns = set()
        
        # Simple pattern extraction - replace numbers and UUIDs with placeholders
        import re
        
        # Replace numbers
        pattern = re.sub(r'\d+', '<NUM>', message)
        patterns.add(pattern)
        
        # Replace UUIDs
        pattern = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', pattern)
        patterns.add(pattern)
        
        # Replace IP addresses
        pattern = re.sub(r'\d+\.\d+\.\d+\.\d+', '<IP>', pattern)
        patterns.add(pattern)
        
        # Replace timestamps
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', pattern)
        patterns.add(pattern)
        
        return patterns
    
    def _cleanup_patterns(self) -> None:
        """Clean up old patterns."""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - 3600  # 1 hour
            
            old_patterns = [
                pattern for pattern, info in self.pattern_cache.items()
                if info['last_seen'] < cutoff_time
            ]
            
            for pattern in old_patterns:
                del self.pattern_cache[pattern]