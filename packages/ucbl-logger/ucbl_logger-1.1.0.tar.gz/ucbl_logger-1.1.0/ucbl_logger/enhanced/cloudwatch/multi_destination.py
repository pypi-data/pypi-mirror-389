"""
Multi-Destination CloudWatch Support

Support for multiple log destinations with parallel delivery and failover.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from enum import Enum

from .interfaces import IMultiDestinationHandler
from .models import LogBatch, LogEntry, DeliveryStats, CloudWatchDestination
from .handler import EnhancedCloudWatchHandler


class DeliveryMode(Enum):
    """Delivery modes for multi-destination."""
    PARALLEL = "parallel"  # Send to all destinations simultaneously
    FAILOVER = "failover"  # Send to primary, failover on failure
    BROADCAST = "broadcast"  # Send to all, continue even if some fail


@dataclass
class DestinationHealth:
    """Health tracking for a destination."""
    name: str
    is_healthy: bool = True
    consecutive_failures: int = 0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0
    
    def record_success(self) -> None:
        """Record a successful delivery."""
        self.is_healthy = True
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        self.total_requests += 1
    
    def record_failure(self) -> None:
        """Record a failed delivery."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        self.total_requests += 1
        self.total_failures += 1
        
        # Mark as unhealthy after 3 consecutive failures
        if self.consecutive_failures >= 3:
            self.is_healthy = False
    
    def get_failure_rate(self) -> float:
        """Get the failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests


class MultiDestinationManager(IMultiDestinationHandler):
    """Manager for multiple CloudWatch destinations."""
    
    def __init__(self, 
                 destinations: List[CloudWatchDestination],
                 delivery_mode: DeliveryMode = DeliveryMode.PARALLEL,
                 max_workers: int = 4):
        
        self.destinations = sorted(destinations, key=lambda d: d.priority)
        self.delivery_mode = delivery_mode
        self.handlers: Dict[str, EnhancedCloudWatchHandler] = {}
        self.health: Dict[str, DestinationHealth] = {}
        
        # Thread pool for parallel delivery
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="multi-dest")
        
        # Statistics
        self.stats: Dict[str, DeliveryStats] = {}
        self.lock = threading.Lock()
        
        # Health monitoring
        self.health_check_interval = 60.0  # seconds
        self.last_health_check = time.time()
        
        # Initialize handlers
        self._initialize_handlers()
    
    def add_destination(self, destination: CloudWatchDestination) -> None:
        """Add a new destination."""
        with self.lock:
            # Insert in priority order
            inserted = False
            for i, existing in enumerate(self.destinations):
                if destination.priority < existing.priority:
                    self.destinations.insert(i, destination)
                    inserted = True
                    break
            
            if not inserted:
                self.destinations.append(destination)
            
            # Initialize handler
            if destination.enabled:
                self.handlers[destination.name] = EnhancedCloudWatchHandler(destination.config)
                self.health[destination.name] = DestinationHealth(destination.name)
                self.stats[destination.name] = DeliveryStats()
    
    def remove_destination(self, destination_name: str) -> None:
        """Remove a destination."""
        with self.lock:
            # Remove from destinations list
            self.destinations = [d for d in self.destinations if d.name != destination_name]
            
            # Shutdown and remove handler
            if destination_name in self.handlers:
                self.handlers[destination_name].shutdown()
                del self.handlers[destination_name]
            
            # Remove health and stats tracking
            if destination_name in self.health:
                del self.health[destination_name]
            
            if destination_name in self.stats:
                del self.stats[destination_name]
    
    def send_to_all(self, batch: LogBatch) -> Dict[str, bool]:
        """Send batch to all destinations according to delivery mode."""
        
        if self.delivery_mode == DeliveryMode.PARALLEL:
            return self._send_parallel(batch)
        elif self.delivery_mode == DeliveryMode.FAILOVER:
            return self._send_failover(batch)
        elif self.delivery_mode == DeliveryMode.BROADCAST:
            return self._send_broadcast(batch)
        else:
            raise ValueError(f"Unknown delivery mode: {self.delivery_mode}")
    
    def send_log_to_all(self, entry: LogEntry) -> Dict[str, bool]:
        """Send single log entry to all destinations."""
        results = {}
        
        for dest in self.destinations:
            if not dest.enabled or dest.name not in self.handlers:
                continue
            
            try:
                success = self.handlers[dest.name].send_log(entry)
                results[dest.name] = success
                
                # Update health
                if success:
                    self.health[dest.name].record_success()
                else:
                    self.health[dest.name].record_failure()
                    
            except Exception as e:
                logging.error(f"Error sending to destination {dest.name}: {e}")
                results[dest.name] = False
                self.health[dest.name].record_failure()
        
        return results
    
    def get_destination_stats(self) -> Dict[str, DeliveryStats]:
        """Get stats for all destinations."""
        with self.lock:
            # Update stats from handlers
            for name, handler in self.handlers.items():
                self.stats[name] = handler.get_stats()
            
            return self.stats.copy()
    
    def get_health_status(self) -> Dict[str, DestinationHealth]:
        """Get health status for all destinations."""
        self._check_health_if_needed()
        
        with self.lock:
            return self.health.copy()
    
    def get_healthy_destinations(self) -> List[str]:
        """Get list of healthy destination names."""
        self._check_health_if_needed()
        
        with self.lock:
            return [name for name, health in self.health.items() if health.is_healthy]
    
    def flush_all(self) -> None:
        """Flush all handlers."""
        for handler in self.handlers.values():
            try:
                handler.flush()
            except Exception as e:
                logging.error(f"Error flushing handler: {e}")
    
    def shutdown(self) -> None:
        """Shutdown all handlers and executor."""
        # Flush all pending logs
        self.flush_all()
        
        # Shutdown handlers
        for handler in self.handlers.values():
            try:
                handler.shutdown()
            except Exception as e:
                logging.error(f"Error shutting down handler: {e}")
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
    
    def _initialize_handlers(self) -> None:
        """Initialize handlers for all enabled destinations."""
        for dest in self.destinations:
            if dest.enabled:
                try:
                    self.handlers[dest.name] = EnhancedCloudWatchHandler(dest.config)
                    self.health[dest.name] = DestinationHealth(dest.name)
                    self.stats[dest.name] = DeliveryStats()
                except Exception as e:
                    logging.error(f"Failed to initialize handler for {dest.name}: {e}")
    
    def _send_parallel(self, batch: LogBatch) -> Dict[str, bool]:
        """Send batch to all destinations in parallel."""
        results = {}
        futures = {}
        
        # Submit all tasks
        for dest in self.destinations:
            if not dest.enabled or dest.name not in self.handlers:
                continue
            
            if not self.health[dest.name].is_healthy:
                # Skip unhealthy destinations in parallel mode
                results[dest.name] = False
                continue
            
            future = self.executor.submit(
                self._send_to_destination, 
                dest.name, 
                batch
            )
            futures[future] = dest.name
        
        # Collect results
        for future in as_completed(futures, timeout=30):
            dest_name = futures[future]
            try:
                success = future.result()
                results[dest_name] = success
                
                # Update health
                if success:
                    self.health[dest_name].record_success()
                else:
                    self.health[dest_name].record_failure()
                    
            except Exception as e:
                logging.error(f"Error in parallel delivery to {dest_name}: {e}")
                results[dest_name] = False
                self.health[dest_name].record_failure()
        
        return results
    
    def _send_failover(self, batch: LogBatch) -> Dict[str, bool]:
        """Send batch with failover logic."""
        results = {}
        
        # Try destinations in priority order
        for dest in self.destinations:
            if not dest.enabled or dest.name not in self.handlers:
                continue
            
            if not self.health[dest.name].is_healthy:
                results[dest.name] = False
                continue
            
            try:
                success = self._send_to_destination(dest.name, batch)
                results[dest.name] = success
                
                if success:
                    self.health[dest.name].record_success()
                    # Success, no need to try other destinations
                    break
                else:
                    self.health[dest.name].record_failure()
                    
            except Exception as e:
                logging.error(f"Error in failover delivery to {dest.name}: {e}")
                results[dest.name] = False
                self.health[dest.name].record_failure()
        
        return results
    
    def _send_broadcast(self, batch: LogBatch) -> Dict[str, bool]:
        """Send batch to all destinations (broadcast mode)."""
        results = {}
        
        # Send to all destinations, regardless of health
        for dest in self.destinations:
            if not dest.enabled or dest.name not in self.handlers:
                continue
            
            try:
                success = self._send_to_destination(dest.name, batch)
                results[dest.name] = success
                
                # Update health
                if success:
                    self.health[dest.name].record_success()
                else:
                    self.health[dest.name].record_failure()
                    
            except Exception as e:
                logging.error(f"Error in broadcast delivery to {dest.name}: {e}")
                results[dest.name] = False
                self.health[dest.name].record_failure()
        
        return results
    
    def _send_to_destination(self, dest_name: str, batch: LogBatch) -> bool:
        """Send batch to a specific destination."""
        handler = self.handlers.get(dest_name)
        if not handler:
            return False
        
        return handler.send_batch(batch)
    
    def _check_health_if_needed(self) -> None:
        """Check health of all destinations if needed."""
        current_time = time.time()
        
        if current_time - self.last_health_check < self.health_check_interval:
            return
        
        with self.lock:
            for name, handler in self.handlers.items():
                try:
                    is_healthy = handler.is_healthy()
                    
                    # Update health status
                    if is_healthy and not self.health[name].is_healthy:
                        # Destination recovered
                        logging.info(f"Destination {name} recovered")
                        self.health[name].is_healthy = True
                        self.health[name].consecutive_failures = 0
                    
                except Exception as e:
                    logging.error(f"Error checking health for {name}: {e}")
                    self.health[name].record_failure()
            
            self.last_health_check = current_time
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all destinations."""
        destination_stats = self.get_destination_stats()
        health_status = self.get_health_status()
        
        summary = {
            'total_destinations': len(self.destinations),
            'healthy_destinations': len(self.get_healthy_destinations()),
            'delivery_mode': self.delivery_mode.value,
            'destinations': {}
        }
        
        for dest in self.destinations:
            dest_summary = {
                'enabled': dest.enabled,
                'priority': dest.priority,
                'healthy': health_status.get(dest.name, DestinationHealth(dest.name)).is_healthy,
                'failure_rate': health_status.get(dest.name, DestinationHealth(dest.name)).get_failure_rate()
            }
            
            if dest.name in destination_stats:
                stats = destination_stats[dest.name]
                dest_summary.update({
                    'total_batches_sent': stats.total_batches_sent,
                    'total_entries_sent': stats.total_entries_sent,
                    'total_failures': stats.total_failures
                })
            
            summary['destinations'][dest.name] = dest_summary
        
        return summary