"""
Data models for performance monitoring
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time


@dataclass
class CPUMetrics:
    """CPU performance metrics"""
    percent: float = 0.0
    per_cpu_percent: List[float] = field(default_factory=list)
    count_logical: int = 0
    count_physical: int = 0
    freq_current: float = 0.0
    freq_min: float = 0.0
    freq_max: float = 0.0
    load_avg_1min: float = 0.0
    load_avg_5min: float = 0.0
    load_avg_15min: float = 0.0


@dataclass
class MemoryMetrics:
    """Memory performance metrics"""
    total: int = 0
    available: int = 0
    percent: float = 0.0
    used: int = 0
    free: int = 0
    active: int = 0
    inactive: int = 0
    buffers: int = 0
    cached: int = 0
    shared: int = 0
    slab: int = 0
    # Virtual memory
    swap_total: int = 0
    swap_used: int = 0
    swap_free: int = 0
    swap_percent: float = 0.0


@dataclass
class DiskMetrics:
    """Disk I/O performance metrics"""
    read_count: int = 0
    write_count: int = 0
    read_bytes: int = 0
    write_bytes: int = 0
    read_time: int = 0
    write_time: int = 0
    busy_time: int = 0
    # Per-second rates (calculated from deltas)
    read_bytes_per_sec: float = 0.0
    write_bytes_per_sec: float = 0.0
    read_ops_per_sec: float = 0.0
    write_ops_per_sec: float = 0.0
    # Disk usage
    total_space: int = 0
    used_space: int = 0
    free_space: int = 0
    usage_percent: float = 0.0


@dataclass
class NetworkMetrics:
    """Network I/O performance metrics"""
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    errin: int = 0
    errout: int = 0
    dropin: int = 0
    dropout: int = 0
    # Per-second rates (calculated from deltas)
    bytes_sent_per_sec: float = 0.0
    bytes_recv_per_sec: float = 0.0
    packets_sent_per_sec: float = 0.0
    packets_recv_per_sec: float = 0.0


@dataclass
class SystemMetrics:
    """Comprehensive system performance metrics"""
    timestamp: float = field(default_factory=time.time)
    cpu: CPUMetrics = field(default_factory=CPUMetrics)
    memory: MemoryMetrics = field(default_factory=MemoryMetrics)
    disk: DiskMetrics = field(default_factory=DiskMetrics)
    network: NetworkMetrics = field(default_factory=NetworkMetrics)
    
    # Legacy fields for backward compatibility
    @property
    def cpu_percent(self) -> float:
        return self.cpu.percent
    
    @property
    def memory_percent(self) -> float:
        return self.memory.percent
    
    @property
    def memory_used_mb(self) -> float:
        return self.memory.used / (1024 * 1024)
    
    @property
    def memory_available_mb(self) -> float:
        return self.memory.available / (1024 * 1024)
    
    @property
    def disk_io_read_mb(self) -> float:
        return self.disk.read_bytes_per_sec / (1024 * 1024)
    
    @property
    def disk_io_write_mb(self) -> float:
        return self.disk.write_bytes_per_sec / (1024 * 1024)
    
    @property
    def network_bytes_sent(self) -> int:
        return self.network.bytes_sent
    
    @property
    def network_bytes_recv(self) -> int:
        return self.network.bytes_recv
    
    @property
    def load_average(self) -> List[float]:
        return [self.cpu.load_avg_1min, self.cpu.load_avg_5min, self.cpu.load_avg_15min]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'timestamp': self.timestamp,
            'cpu': {
                'percent': self.cpu.percent,
                'per_cpu_percent': self.cpu.per_cpu_percent,
                'count_logical': self.cpu.count_logical,
                'count_physical': self.cpu.count_physical,
                'freq_current': self.cpu.freq_current,
                'load_avg_1min': self.cpu.load_avg_1min,
                'load_avg_5min': self.cpu.load_avg_5min,
                'load_avg_15min': self.cpu.load_avg_15min,
            },
            'memory': {
                'total_mb': self.memory.total / (1024 * 1024),
                'available_mb': self.memory.available / (1024 * 1024),
                'percent': self.memory.percent,
                'used_mb': self.memory.used / (1024 * 1024),
                'free_mb': self.memory.free / (1024 * 1024),
                'active_mb': self.memory.active / (1024 * 1024),
                'cached_mb': self.memory.cached / (1024 * 1024),
                'swap_total_mb': self.memory.swap_total / (1024 * 1024),
                'swap_used_mb': self.memory.swap_used / (1024 * 1024),
                'swap_percent': self.memory.swap_percent,
            },
            'disk': {
                'read_bytes_per_sec': self.disk.read_bytes_per_sec,
                'write_bytes_per_sec': self.disk.write_bytes_per_sec,
                'read_ops_per_sec': self.disk.read_ops_per_sec,
                'write_ops_per_sec': self.disk.write_ops_per_sec,
                'total_space_gb': self.disk.total_space / (1024 * 1024 * 1024),
                'used_space_gb': self.disk.used_space / (1024 * 1024 * 1024),
                'free_space_gb': self.disk.free_space / (1024 * 1024 * 1024),
                'usage_percent': self.disk.usage_percent,
            },
            'network': {
                'bytes_sent_per_sec': self.network.bytes_sent_per_sec,
                'bytes_recv_per_sec': self.network.bytes_recv_per_sec,
                'packets_sent_per_sec': self.network.packets_sent_per_sec,
                'packets_recv_per_sec': self.network.packets_recv_per_sec,
                'errors_in': self.network.errin,
                'errors_out': self.network.errout,
                'drops_in': self.network.dropin,
                'drops_out': self.network.dropout,
            }
        }


@dataclass
class PerformanceAlert:
    """Performance alert information"""
    level: str  # 'warning' or 'critical'
    metric: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceThresholds:
    """Comprehensive performance monitoring thresholds"""
    # CPU thresholds
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    load_average_warning: float = 2.0
    load_average_critical: float = 5.0
    
    # Memory thresholds
    memory_warning_percent: float = 80.0
    memory_critical_percent: float = 95.0
    swap_warning_percent: float = 50.0
    swap_critical_percent: float = 80.0
    
    # Disk thresholds
    disk_io_warning_mb_per_sec: float = 100.0
    disk_io_critical_mb_per_sec: float = 200.0
    disk_usage_warning_percent: float = 85.0
    disk_usage_critical_percent: float = 95.0
    disk_ops_warning_per_sec: float = 1000.0
    disk_ops_critical_per_sec: float = 2000.0
    
    # Network thresholds
    network_bandwidth_warning_mbps: float = 100.0
    network_bandwidth_critical_mbps: float = 500.0
    network_packets_warning_per_sec: float = 10000.0
    network_packets_critical_per_sec: float = 50000.0
    network_errors_warning_per_sec: float = 10.0
    network_errors_critical_per_sec: float = 100.0
    network_drops_warning_per_sec: float = 5.0
    network_drops_critical_per_sec: float = 50.0
    
    # Advanced thresholds
    context_switches_warning_per_sec: float = 10000.0
    context_switches_critical_per_sec: float = 50000.0
    interrupts_warning_per_sec: float = 5000.0
    interrupts_critical_per_sec: float = 25000.0
    
    def check_cpu_threshold(self, cpu_percent: float) -> Optional[PerformanceAlert]:
        """Check CPU threshold and return alert if exceeded"""
        if cpu_percent >= self.cpu_critical_percent:
            return PerformanceAlert(
                level="critical",
                metric="cpu_percent",
                current_value=cpu_percent,
                threshold_value=self.cpu_critical_percent,
                message=f"CPU usage critical: {cpu_percent:.1f}% >= {self.cpu_critical_percent}%"
            )
        elif cpu_percent >= self.cpu_warning_percent:
            return PerformanceAlert(
                level="warning",
                metric="cpu_percent",
                current_value=cpu_percent,
                threshold_value=self.cpu_warning_percent,
                message=f"CPU usage warning: {cpu_percent:.1f}% >= {self.cpu_warning_percent}%"
            )
        return None
    
    def check_memory_threshold(self, memory_percent: float) -> Optional[PerformanceAlert]:
        """Check memory threshold and return alert if exceeded"""
        if memory_percent >= self.memory_critical_percent:
            return PerformanceAlert(
                level="critical",
                metric="memory_percent",
                current_value=memory_percent,
                threshold_value=self.memory_critical_percent,
                message=f"Memory usage critical: {memory_percent:.1f}% >= {self.memory_critical_percent}%"
            )
        elif memory_percent >= self.memory_warning_percent:
            return PerformanceAlert(
                level="warning",
                metric="memory_percent",
                current_value=memory_percent,
                threshold_value=self.memory_warning_percent,
                message=f"Memory usage warning: {memory_percent:.1f}% >= {self.memory_warning_percent}%"
            )
        return None
    
    def check_swap_threshold(self, swap_percent: float) -> Optional[PerformanceAlert]:
        """Check swap usage threshold and return alert if exceeded"""
        if swap_percent >= self.swap_critical_percent:
            return PerformanceAlert(
                level="critical",
                metric="swap_percent",
                current_value=swap_percent,
                threshold_value=self.swap_critical_percent,
                message=f"Swap usage critical: {swap_percent:.1f}% >= {self.swap_critical_percent}%"
            )
        elif swap_percent >= self.swap_warning_percent:
            return PerformanceAlert(
                level="warning",
                metric="swap_percent",
                current_value=swap_percent,
                threshold_value=self.swap_warning_percent,
                message=f"Swap usage warning: {swap_percent:.1f}% >= {self.swap_warning_percent}%"
            )
        return None
    
    def check_load_average_threshold(self, load_avg: float) -> Optional[PerformanceAlert]:
        """Check load average threshold and return alert if exceeded"""
        if load_avg >= self.load_average_critical:
            return PerformanceAlert(
                level="critical",
                metric="load_average",
                current_value=load_avg,
                threshold_value=self.load_average_critical,
                message=f"Load average critical: {load_avg:.2f} >= {self.load_average_critical}"
            )
        elif load_avg >= self.load_average_warning:
            return PerformanceAlert(
                level="warning",
                metric="load_average",
                current_value=load_avg,
                threshold_value=self.load_average_warning,
                message=f"Load average warning: {load_avg:.2f} >= {self.load_average_warning}"
            )
        return None
    
    def check_disk_io_threshold(self, io_mbps: float) -> Optional[PerformanceAlert]:
        """Check disk I/O threshold and return alert if exceeded"""
        if io_mbps >= self.disk_io_critical_mb_per_sec:
            return PerformanceAlert(
                level="critical",
                metric="disk_io_mbps",
                current_value=io_mbps,
                threshold_value=self.disk_io_critical_mb_per_sec,
                message=f"Disk I/O critical: {io_mbps:.1f} MB/s >= {self.disk_io_critical_mb_per_sec} MB/s"
            )
        elif io_mbps >= self.disk_io_warning_mb_per_sec:
            return PerformanceAlert(
                level="warning",
                metric="disk_io_mbps",
                current_value=io_mbps,
                threshold_value=self.disk_io_warning_mb_per_sec,
                message=f"Disk I/O warning: {io_mbps:.1f} MB/s >= {self.disk_io_warning_mb_per_sec} MB/s"
            )
        return None
    
    def check_disk_usage_threshold(self, usage_percent: float) -> Optional[PerformanceAlert]:
        """Check disk usage threshold and return alert if exceeded"""
        if usage_percent >= self.disk_usage_critical_percent:
            return PerformanceAlert(
                level="critical",
                metric="disk_usage_percent",
                current_value=usage_percent,
                threshold_value=self.disk_usage_critical_percent,
                message=f"Disk usage critical: {usage_percent:.1f}% >= {self.disk_usage_critical_percent}%"
            )
        elif usage_percent >= self.disk_usage_warning_percent:
            return PerformanceAlert(
                level="warning",
                metric="disk_usage_percent",
                current_value=usage_percent,
                threshold_value=self.disk_usage_warning_percent,
                message=f"Disk usage warning: {usage_percent:.1f}% >= {self.disk_usage_warning_percent}%"
            )
        return None
    
    def check_network_bandwidth_threshold(self, bandwidth_mbps: float) -> Optional[PerformanceAlert]:
        """Check network bandwidth threshold and return alert if exceeded"""
        if bandwidth_mbps >= self.network_bandwidth_critical_mbps:
            return PerformanceAlert(
                level="critical",
                metric="network_bandwidth_mbps",
                current_value=bandwidth_mbps,
                threshold_value=self.network_bandwidth_critical_mbps,
                message=f"Network bandwidth critical: {bandwidth_mbps:.1f} Mbps >= {self.network_bandwidth_critical_mbps} Mbps"
            )
        elif bandwidth_mbps >= self.network_bandwidth_warning_mbps:
            return PerformanceAlert(
                level="warning",
                metric="network_bandwidth_mbps",
                current_value=bandwidth_mbps,
                threshold_value=self.network_bandwidth_warning_mbps,
                message=f"Network bandwidth warning: {bandwidth_mbps:.1f} Mbps >= {self.network_bandwidth_warning_mbps} Mbps"
            )
        return None
    
    def check_network_errors_threshold(self, errors_per_sec: float) -> Optional[PerformanceAlert]:
        """Check network errors threshold and return alert if exceeded"""
        if errors_per_sec >= self.network_errors_critical_per_sec:
            return PerformanceAlert(
                level="critical",
                metric="network_errors_per_sec",
                current_value=errors_per_sec,
                threshold_value=self.network_errors_critical_per_sec,
                message=f"Network errors critical: {errors_per_sec:.1f}/s >= {self.network_errors_critical_per_sec}/s"
            )
        elif errors_per_sec >= self.network_errors_warning_per_sec:
            return PerformanceAlert(
                level="warning",
                metric="network_errors_per_sec",
                current_value=errors_per_sec,
                threshold_value=self.network_errors_warning_per_sec,
                message=f"Network errors warning: {errors_per_sec:.1f}/s >= {self.network_errors_warning_per_sec}/s"
            )
        return None