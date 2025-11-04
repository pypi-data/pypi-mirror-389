"""
Enhanced performance monitor with real system metrics collection using psutil
"""

import time
import threading
import logging
from typing import List, Dict, Optional, Tuple
from collections import deque
from .interfaces import IPerformanceMonitor
from .models import (
    SystemMetrics, PerformanceThresholds, CPUMetrics, 
    MemoryMetrics, DiskMetrics, NetworkMetrics, PerformanceAlert
)

try:
    import psutil
except ImportError:
    psutil = None


class EnhancedPerformanceMonitor(IPerformanceMonitor):
    """Enhanced performance monitor with real system metrics collection"""
    
    def __init__(self, 
                 thresholds: PerformanceThresholds = None,
                 collection_interval: int = 60,
                 history_size: int = 100):
        """
        Initialize enhanced performance monitor
        
        Args:
            thresholds: Performance thresholds for alerting
            collection_interval: Interval in seconds for background collection
            history_size: Number of historical metrics to keep
        """
        self.thresholds = thresholds or PerformanceThresholds()
        self.collection_interval = collection_interval
        self.history_size = history_size
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=history_size)
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Previous metrics for calculating rates
        self._prev_disk_metrics: Optional[Dict] = None
        self._prev_network_metrics: Optional[Dict] = None
        self._prev_timestamp: Optional[float] = None
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Check psutil availability
        if psutil is None:
            self.logger.warning("psutil not available, using mock metrics")
            self._use_mock_metrics = True
        else:
            self._use_mock_metrics = False
    
    def collect_cpu_metrics(self) -> CPUMetrics:
        """Collect comprehensive CPU metrics"""
        if self._use_mock_metrics:
            return CPUMetrics(
                percent=10.0,
                per_cpu_percent=[8.0, 12.0],
                count_logical=2,
                count_physical=2,
                load_avg_1min=0.5,
                load_avg_5min=0.3,
                load_avg_15min=0.2
            )
        
        try:
            # CPU percentage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # CPU counts
            count_logical = psutil.cpu_count(logical=True)
            count_physical = psutil.cpu_count(logical=False)
            
            # CPU frequency
            freq_info = psutil.cpu_freq()
            freq_current = freq_info.current if freq_info else 0.0
            freq_min = freq_info.min if freq_info else 0.0
            freq_max = freq_info.max if freq_info else 0.0
            
            # Load average (Unix-like systems only)
            load_avg_1min = load_avg_5min = load_avg_15min = 0.0
            try:
                load_avg = psutil.getloadavg()
                load_avg_1min, load_avg_5min, load_avg_15min = load_avg
            except (AttributeError, OSError):
                # getloadavg not available on Windows
                pass
            
            return CPUMetrics(
                percent=cpu_percent,
                per_cpu_percent=per_cpu_percent,
                count_logical=count_logical or 0,
                count_physical=count_physical or 0,
                freq_current=freq_current,
                freq_min=freq_min,
                freq_max=freq_max,
                load_avg_1min=load_avg_1min,
                load_avg_5min=load_avg_5min,
                load_avg_15min=load_avg_15min
            )
        except Exception as e:
            self.logger.error(f"Error collecting CPU metrics: {e}")
            return CPUMetrics()
    
    def collect_memory_metrics(self) -> MemoryMetrics:
        """Collect comprehensive memory metrics including RSS, VMS, and swap"""
        if self._use_mock_metrics:
            return MemoryMetrics(
                total=8 * 1024 * 1024 * 1024,  # 8GB
                available=4 * 1024 * 1024 * 1024,  # 4GB
                percent=50.0,
                used=4 * 1024 * 1024 * 1024,  # 4GB
                free=4 * 1024 * 1024 * 1024,  # 4GB
            )
        
        try:
            # Virtual memory
            vmem = psutil.virtual_memory()
            
            # Swap memory
            swap = psutil.swap_memory()
            
            return MemoryMetrics(
                total=vmem.total,
                available=vmem.available,
                percent=vmem.percent,
                used=vmem.used,
                free=vmem.free,
                active=getattr(vmem, 'active', 0),
                inactive=getattr(vmem, 'inactive', 0),
                buffers=getattr(vmem, 'buffers', 0),
                cached=getattr(vmem, 'cached', 0),
                shared=getattr(vmem, 'shared', 0),
                slab=getattr(vmem, 'slab', 0),
                swap_total=swap.total,
                swap_used=swap.used,
                swap_free=swap.free,
                swap_percent=swap.percent
            )
        except Exception as e:
            self.logger.error(f"Error collecting memory metrics: {e}")
            return MemoryMetrics()
    
    def collect_disk_metrics(self) -> DiskMetrics:
        """Collect comprehensive disk I/O metrics for container filesystem"""
        if self._use_mock_metrics:
            return DiskMetrics(
                read_bytes_per_sec=1024 * 1024,  # 1MB/s
                write_bytes_per_sec=512 * 1024,  # 512KB/s
                total_space=100 * 1024 * 1024 * 1024,  # 100GB
                used_space=50 * 1024 * 1024 * 1024,  # 50GB
                free_space=50 * 1024 * 1024 * 1024,  # 50GB
                usage_percent=50.0
            )
        
        try:
            current_time = time.time()
            
            # Disk I/O counters
            disk_io = psutil.disk_io_counters()
            if disk_io is None:
                return DiskMetrics()
            
            # Disk usage for root filesystem
            disk_usage = psutil.disk_usage('/')
            
            # Calculate per-second rates if we have previous metrics
            read_bytes_per_sec = write_bytes_per_sec = 0.0
            read_ops_per_sec = write_ops_per_sec = 0.0
            
            if self._prev_disk_metrics and self._prev_timestamp:
                time_delta = current_time - self._prev_timestamp
                if time_delta > 0:
                    read_bytes_per_sec = (disk_io.read_bytes - self._prev_disk_metrics['read_bytes']) / time_delta
                    write_bytes_per_sec = (disk_io.write_bytes - self._prev_disk_metrics['write_bytes']) / time_delta
                    read_ops_per_sec = (disk_io.read_count - self._prev_disk_metrics['read_count']) / time_delta
                    write_ops_per_sec = (disk_io.write_count - self._prev_disk_metrics['write_count']) / time_delta
            
            # Store current metrics for next calculation
            self._prev_disk_metrics = {
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count
            }
            
            return DiskMetrics(
                read_count=disk_io.read_count,
                write_count=disk_io.write_count,
                read_bytes=disk_io.read_bytes,
                write_bytes=disk_io.write_bytes,
                read_time=disk_io.read_time,
                write_time=disk_io.write_time,
                busy_time=getattr(disk_io, 'busy_time', 0),
                read_bytes_per_sec=max(0, read_bytes_per_sec),
                write_bytes_per_sec=max(0, write_bytes_per_sec),
                read_ops_per_sec=max(0, read_ops_per_sec),
                write_ops_per_sec=max(0, write_ops_per_sec),
                total_space=disk_usage.total,
                used_space=disk_usage.used,
                free_space=disk_usage.free,
                usage_percent=(disk_usage.used / disk_usage.total) * 100 if disk_usage.total > 0 else 0.0
            )
        except Exception as e:
            self.logger.error(f"Error collecting disk metrics: {e}")
            return DiskMetrics()
    
    def collect_network_metrics(self) -> NetworkMetrics:
        """Collect detailed network I/O statistics for container interfaces"""
        if self._use_mock_metrics:
            return NetworkMetrics(
                bytes_sent_per_sec=1024 * 100,  # 100KB/s
                bytes_recv_per_sec=1024 * 200,  # 200KB/s
                packets_sent_per_sec=10,
                packets_recv_per_sec=20
            )
        
        try:
            current_time = time.time()
            
            # Network I/O counters
            net_io = psutil.net_io_counters()
            if net_io is None:
                return NetworkMetrics()
            
            # Calculate per-second rates if we have previous metrics
            bytes_sent_per_sec = bytes_recv_per_sec = 0.0
            packets_sent_per_sec = packets_recv_per_sec = 0.0
            
            if self._prev_network_metrics and self._prev_timestamp:
                time_delta = current_time - self._prev_timestamp
                if time_delta > 0:
                    bytes_sent_per_sec = (net_io.bytes_sent - self._prev_network_metrics['bytes_sent']) / time_delta
                    bytes_recv_per_sec = (net_io.bytes_recv - self._prev_network_metrics['bytes_recv']) / time_delta
                    packets_sent_per_sec = (net_io.packets_sent - self._prev_network_metrics['packets_sent']) / time_delta
                    packets_recv_per_sec = (net_io.packets_recv - self._prev_network_metrics['packets_recv']) / time_delta
            
            # Store current metrics for next calculation
            self._prev_network_metrics = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
            # Update timestamp for rate calculations
            self._prev_timestamp = current_time
            
            return NetworkMetrics(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                errin=net_io.errin,
                errout=net_io.errout,
                dropin=net_io.dropin,
                dropout=net_io.dropout,
                bytes_sent_per_sec=max(0, bytes_sent_per_sec),
                bytes_recv_per_sec=max(0, bytes_recv_per_sec),
                packets_sent_per_sec=max(0, packets_sent_per_sec),
                packets_recv_per_sec=max(0, packets_recv_per_sec)
            )
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
            return NetworkMetrics()
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system performance metrics"""
        try:
            cpu_metrics = self.collect_cpu_metrics()
            memory_metrics = self.collect_memory_metrics()
            disk_metrics = self.collect_disk_metrics()
            network_metrics = self.collect_network_metrics()
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu=cpu_metrics,
                memory=memory_metrics,
                disk=disk_metrics,
                network=network_metrics
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics()
    
    def check_performance_thresholds(self, metrics: SystemMetrics) -> List[PerformanceAlert]:
        """Check if metrics exceed configured thresholds and return alerts"""
        alerts = []
        
        try:
            # CPU threshold checks
            cpu_alert = self.thresholds.check_cpu_threshold(metrics.cpu.percent)
            if cpu_alert:
                alerts.append(cpu_alert)
            
            # Memory threshold checks
            memory_alert = self.thresholds.check_memory_threshold(metrics.memory.percent)
            if memory_alert:
                alerts.append(memory_alert)
            
            # Swap threshold checks
            swap_alert = self.thresholds.check_swap_threshold(metrics.memory.swap_percent)
            if swap_alert:
                alerts.append(swap_alert)
            
            # Load average threshold checks
            load_alert = self.thresholds.check_load_average_threshold(metrics.cpu.load_avg_1min)
            if load_alert:
                alerts.append(load_alert)
            
            # Disk I/O threshold checks
            disk_io_total = metrics.disk.read_bytes_per_sec + metrics.disk.write_bytes_per_sec
            disk_io_mb_per_sec = disk_io_total / (1024 * 1024)
            disk_io_alert = self.thresholds.check_disk_io_threshold(disk_io_mb_per_sec)
            if disk_io_alert:
                alerts.append(disk_io_alert)
            
            # Disk usage threshold checks
            disk_usage_alert = self.thresholds.check_disk_usage_threshold(metrics.disk.usage_percent)
            if disk_usage_alert:
                alerts.append(disk_usage_alert)
            
            # Network bandwidth threshold checks
            network_bandwidth_total = metrics.network.bytes_sent_per_sec + metrics.network.bytes_recv_per_sec
            network_bandwidth_mbps = (network_bandwidth_total * 8) / (1024 * 1024)  # Convert to Mbps
            network_bandwidth_alert = self.thresholds.check_network_bandwidth_threshold(network_bandwidth_mbps)
            if network_bandwidth_alert:
                alerts.append(network_bandwidth_alert)
            
            # Network errors threshold checks
            network_errors_total = metrics.network.errin + metrics.network.errout
            # Estimate errors per second (this is cumulative, so we'd need rate calculation)
            # For now, we'll use a simple heuristic
            if hasattr(self, '_prev_network_errors') and self._prev_timestamp:
                time_delta = metrics.timestamp - self._prev_timestamp
                if time_delta > 0:
                    errors_per_sec = (network_errors_total - self._prev_network_errors) / time_delta
                    network_errors_alert = self.thresholds.check_network_errors_threshold(errors_per_sec)
                    if network_errors_alert:
                        alerts.append(network_errors_alert)
            
            self._prev_network_errors = network_errors_total
            
        except Exception as e:
            self.logger.error(f"Error checking performance thresholds: {e}")
        
        return alerts
    
    def get_metrics_history(self, duration_seconds: int = 300) -> List[SystemMetrics]:
        """Get historical metrics for specified duration"""
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self.collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.collection_interval)
    
    def start_monitoring(self) -> None:
        """Start background performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="PerformanceMonitor"
            )
            self.monitoring_thread.start()
            self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background performance monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            self.logger.info("Performance monitoring stopped")
    
    def collect_network_interface_metrics(self) -> Dict[str, Dict[str, float]]:
        """Collect detailed network metrics per interface"""
        if self._use_mock_metrics:
            return {
                'eth0': {
                    'bytes_sent_per_sec': 1024 * 100,
                    'bytes_recv_per_sec': 1024 * 200,
                    'packets_sent_per_sec': 10,
                    'packets_recv_per_sec': 20,
                    'errors_in': 0,
                    'errors_out': 0,
                    'drops_in': 0,
                    'drops_out': 0
                }
            }
        
        try:
            interface_metrics = {}
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            current_time = time.time()
            
            for interface, stats in net_io_per_nic.items():
                # Skip loopback and inactive interfaces
                if interface.startswith('lo') or stats.bytes_sent == 0 and stats.bytes_recv == 0:
                    continue
                
                # Calculate per-second rates if we have previous data
                bytes_sent_per_sec = bytes_recv_per_sec = 0.0
                packets_sent_per_sec = packets_recv_per_sec = 0.0
                
                prev_key = f"_prev_net_{interface}"
                if hasattr(self, prev_key) and self._prev_timestamp:
                    prev_stats = getattr(self, prev_key)
                    time_delta = current_time - self._prev_timestamp
                    if time_delta > 0:
                        bytes_sent_per_sec = (stats.bytes_sent - prev_stats['bytes_sent']) / time_delta
                        bytes_recv_per_sec = (stats.bytes_recv - prev_stats['bytes_recv']) / time_delta
                        packets_sent_per_sec = (stats.packets_sent - prev_stats['packets_sent']) / time_delta
                        packets_recv_per_sec = (stats.packets_recv - prev_stats['packets_recv']) / time_delta
                
                # Store current stats for next calculation
                setattr(self, prev_key, {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv
                })
                
                interface_metrics[interface] = {
                    'bytes_sent_per_sec': max(0, bytes_sent_per_sec),
                    'bytes_recv_per_sec': max(0, bytes_recv_per_sec),
                    'packets_sent_per_sec': max(0, packets_sent_per_sec),
                    'packets_recv_per_sec': max(0, packets_recv_per_sec),
                    'errors_in': stats.errin,
                    'errors_out': stats.errout,
                    'drops_in': stats.dropin,
                    'drops_out': stats.dropout
                }
            
            return interface_metrics
        except Exception as e:
            self.logger.error(f"Error collecting network interface metrics: {e}")
            return {}
    
    def generate_performance_alerts(self, metrics: SystemMetrics) -> List[PerformanceAlert]:
        """Generate performance alerts with automatic threshold breach detection"""
        alerts = self.check_performance_thresholds(metrics)
        
        # Add custom alert logic for container-specific scenarios
        try:
            # Check for container memory pressure
            if metrics.memory.percent > 90 and metrics.memory.swap_percent > 50:
                alerts.append(PerformanceAlert(
                    level="critical",
                    metric="container_memory_pressure",
                    current_value=metrics.memory.percent,
                    threshold_value=90.0,
                    message=f"Container memory pressure detected: {metrics.memory.percent:.1f}% memory + {metrics.memory.swap_percent:.1f}% swap"
                ))
            
            # Check for I/O wait issues
            if metrics.cpu.load_avg_1min > metrics.cpu.count_logical * 2:
                alerts.append(PerformanceAlert(
                    level="warning",
                    metric="high_load_average",
                    current_value=metrics.cpu.load_avg_1min,
                    threshold_value=metrics.cpu.count_logical * 2,
                    message=f"High load average detected: {metrics.cpu.load_avg_1min:.2f} on {metrics.cpu.count_logical} cores"
                ))
            
            # Check for network interface saturation
            interface_metrics = self.collect_network_interface_metrics()
            for interface, stats in interface_metrics.items():
                total_bandwidth = (stats['bytes_sent_per_sec'] + stats['bytes_recv_per_sec']) * 8 / (1024 * 1024)  # Mbps
                if total_bandwidth > 800:  # Assuming 1Gbps interface
                    alerts.append(PerformanceAlert(
                        level="warning",
                        metric=f"network_interface_{interface}_saturation",
                        current_value=total_bandwidth,
                        threshold_value=800.0,
                        message=f"Network interface {interface} approaching saturation: {total_bandwidth:.1f} Mbps"
                    ))
        
        except Exception as e:
            self.logger.error(f"Error generating custom performance alerts: {e}")
        
        return alerts
    
    def get_current_load_summary(self) -> Dict[str, float]:
        """Get a summary of current system load"""
        try:
            metrics = self.collect_system_metrics()
            return {
                'cpu_percent': metrics.cpu.percent,
                'memory_percent': metrics.memory.percent,
                'disk_usage_percent': metrics.disk.usage_percent,
                'load_avg_1min': metrics.cpu.load_avg_1min,
                'network_mbps_total': (metrics.network.bytes_sent_per_sec + metrics.network.bytes_recv_per_sec) / (1024 * 1024)
            }
        except Exception as e:
            self.logger.error(f"Error getting load summary: {e}")
            return {}