"""
Advanced security monitoring for container runtime security events
"""

import os
import time
import json
import logging
import threading
import subprocess
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from .models import RuntimeSecurityEvent, SecurityEventSeverity, SecurityEventType


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    timestamp: float
    alert_type: str
    severity: str
    description: str
    source: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'description': self.description,
            'source': self.source,
            'metadata': self.metadata
        }


class RuntimeSecurityMonitor:
    """Advanced container runtime security event monitor"""
    
    def __init__(self, alert_callback: Optional[Callable[[SecurityAlert], None]] = None):
        """
        Initialize runtime security monitor
        
        Args:
            alert_callback: Callback function for security alerts
        """
        self.logger = logging.getLogger(__name__)
        self.alert_callback = alert_callback
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._security_events: List[RuntimeSecurityEvent] = []
        
        # Security monitoring configuration
        self.monitor_config = {
            'file_access_monitoring': True,
            'process_monitoring': True,
            'network_monitoring': True,
            'capability_monitoring': True,
            'syscall_monitoring': False,  # Requires special privileges
            'container_escape_detection': True
        }
        
        # Initialize whitelist configuration
        self._init_whitelist_config()
        
        # Initialize monitoring tools
        self._init_monitoring_tools()
    
    def _init_whitelist_config(self) -> None:
        """Initialize security whitelist configuration from environment variables"""
        # Kubernetes-aware mode
        self.kubernetes_mode = os.getenv('UCBL_SECURITY_KUBERNETES_MODE', 'true').lower() == 'true'
        
        # Default Kubernetes whitelists
        self.k8s_allowed_mounts = {
            '/run/secrets/kubernetes.io/serviceaccount',
            '/run/secrets/eks.amazonaws.com/serviceaccount',
            '/var/run/secrets/kubernetes.io',
            '/var/run/secrets/istio',
            '/etc/istio',
            '/tmp',
            '/var/tmp',
            '/proc',
            '/sys',
            '/dev/shm'
        }
        
        self.k8s_allowed_fs_types = {'overlay', 'tmpfs', 'proc', 'sysfs', 'devtmpfs'}
        
        self.k8s_allowed_devices = {'overlay', 'tmpfs', 'proc', 'sysfs', 'devtmpfs', 'shm'}
        
        # User-defined whitelists (override/extend defaults)
        custom_mounts = os.getenv('UCBL_SECURITY_ALLOWED_MOUNTS', '')
        if custom_mounts:
            self.allowed_mounts = set(custom_mounts.split(','))
        elif self.kubernetes_mode:
            self.allowed_mounts = self.k8s_allowed_mounts
        else:
            self.allowed_mounts = set()
        
        custom_fs_types = os.getenv('UCBL_SECURITY_ALLOWED_FS_TYPES', '')
        if custom_fs_types:
            self.allowed_fs_types = set(custom_fs_types.split(','))
        elif self.kubernetes_mode:
            self.allowed_fs_types = self.k8s_allowed_fs_types
        else:
            self.allowed_fs_types = set()
        
        custom_devices = os.getenv('UCBL_SECURITY_ALLOWED_DEVICES', '')
        if custom_devices:
            self.allowed_devices = set(custom_devices.split(','))
        elif self.kubernetes_mode:
            self.allowed_devices = self.k8s_allowed_devices
        else:
            self.allowed_devices = set()
        
        self.logger.info(f"Security whitelist initialized (K8s mode: {self.kubernetes_mode})")
        self.logger.debug(f"Allowed mounts: {len(self.allowed_mounts)} entries")
        self.logger.debug(f"Allowed FS types: {self.allowed_fs_types}")
        self.logger.debug(f"Allowed devices: {self.allowed_devices}")
    
    def _init_monitoring_tools(self) -> None:
        """Initialize available security monitoring tools"""
        self.available_tools = {}
        
        # Check for Falco
        if self._check_tool_availability('falco'):
            self.available_tools['falco'] = {
                'binary': '/usr/bin/falco',
                'config': '/etc/falco/falco.yaml',
                'rules': '/etc/falco/falco_rules.yaml'
            }
        
        # Check for auditd
        if self._check_tool_availability('auditctl'):
            self.available_tools['auditd'] = {
                'binary': '/sbin/auditctl',
                'log_path': '/var/log/audit/audit.log'
            }
        
        # Check for sysdig
        if self._check_tool_availability('sysdig'):
            self.available_tools['sysdig'] = {
                'binary': '/usr/bin/sysdig'
            }
        
        self.logger.info(f"Initialized security monitoring tools: {list(self.available_tools.keys())}")
    
    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a security monitoring tool is available"""
        try:
            result = subprocess.run(['which', tool], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def start_monitoring(self) -> None:
        """Start runtime security monitoring"""
        if self._monitoring:
            self.logger.warning("Security monitoring already running")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info("Started runtime security monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop runtime security monitoring"""
        self._monitoring = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        self.logger.info("Stopped runtime security monitoring")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                # Monitor different security aspects
                if self.monitor_config['file_access_monitoring']:
                    self._monitor_file_access()
                
                if self.monitor_config['process_monitoring']:
                    self._monitor_processes()
                
                if self.monitor_config['network_monitoring']:
                    self._monitor_network_activity()
                
                if self.monitor_config['capability_monitoring']:
                    self._monitor_capabilities()
                
                if self.monitor_config['container_escape_detection']:
                    self._detect_container_escape_attempts()
                
                # Sleep between monitoring cycles
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in security monitoring loop: {e}")
                time.sleep(5)  # Longer sleep on error
    
    def _monitor_file_access(self) -> None:
        """Monitor suspicious file access patterns"""
        try:
            # Monitor access to sensitive files
            sensitive_files = [
                '/etc/passwd', '/etc/shadow', '/etc/group', '/etc/sudoers',
                '/root/.ssh/', '/home/*/.ssh/', '/var/run/docker.sock',
                '/proc/*/mem', '/dev/mem', '/dev/kmem'
            ]
            
            # Check for recent access to sensitive files
            for file_pattern in sensitive_files:
                if '*' not in file_pattern and Path(file_pattern).exists():
                    stat_info = Path(file_pattern).stat()
                    
                    # Check if file was accessed recently (within last 60 seconds)
                    if time.time() - stat_info.st_atime < 60:
                        self._create_security_alert(
                            alert_type='sensitive_file_access',
                            severity='HIGH',
                            description=f'Recent access to sensitive file: {file_pattern}',
                            source='file_monitor',
                            metadata={
                                'file_path': file_pattern,
                                'access_time': stat_info.st_atime,
                                'file_mode': oct(stat_info.st_mode)
                            }
                        )
        
        except Exception as e:
            self.logger.debug(f"Error monitoring file access: {e}")
    
    def _monitor_processes(self) -> None:
        """Monitor for suspicious process activity"""
        try:
            # Check for suspicious processes
            suspicious_commands = [
                'nc', 'netcat', 'ncat',  # Network tools
                'wget', 'curl',  # Download tools
                'python -c', 'perl -e', 'ruby -e',  # Inline scripts
                'base64 -d', 'xxd -r',  # Decoding tools
                'chmod +x', 'chmod 777',  # Permission changes
                'su -', 'sudo su',  # Privilege escalation
                '/bin/sh', '/bin/bash'  # Shell access
            ]
            
            # Read current processes
            try:
                with open('/proc/self/stat', 'r') as f:
                    stat_line = f.read().strip()
                    
                # Parse process information
                parts = stat_line.split()
                if len(parts) >= 2:
                    comm = parts[1].strip('()')
                    
                    # Check if current process command is suspicious
                    for suspicious_cmd in suspicious_commands:
                        if suspicious_cmd in comm:
                            self._create_security_alert(
                                alert_type='suspicious_process',
                                severity='MEDIUM',
                                description=f'Suspicious process detected: {comm}',
                                source='process_monitor',
                                metadata={
                                    'command': comm,
                                    'pid': os.getpid(),
                                    'ppid': os.getppid() if hasattr(os, 'getppid') else None
                                }
                            )
            
            except (FileNotFoundError, IOError):
                pass
        
        except Exception as e:
            self.logger.debug(f"Error monitoring processes: {e}")
    
    def _monitor_network_activity(self) -> None:
        """Monitor for suspicious network activity"""
        try:
            # Check for unusual network connections
            suspicious_ports = [4444, 5555, 6666, 7777, 8888, 9999]  # Common backdoor ports
            
            # Read network connections
            try:
                with open('/proc/net/tcp', 'r') as f:
                    lines = f.readlines()[1:]  # Skip header
                    
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        local_address = parts[1]
                        state = parts[3]
                        
                        # Parse port from address
                        if ':' in local_address:
                            port_hex = local_address.split(':')[1]
                            port = int(port_hex, 16)
                            
                            # Check for suspicious listening ports
                            if state == '0A' and port in suspicious_ports:  # LISTEN state
                                self._create_security_alert(
                                    alert_type='suspicious_network_activity',
                                    severity='HIGH',
                                    description=f'Suspicious listening port detected: {port}',
                                    source='network_monitor',
                                    metadata={
                                        'port': port,
                                        'local_address': local_address,
                                        'state': state
                                    }
                                )
            
            except (FileNotFoundError, IOError):
                pass
        
        except Exception as e:
            self.logger.debug(f"Error monitoring network activity: {e}")
    
    def _monitor_capabilities(self) -> None:
        """Monitor for capability changes and dangerous capabilities"""
        try:
            # Read current capabilities
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('Cap'):
                        parts = line.strip().split('\t')
                        if len(parts) == 2:
                            cap_type = parts[0].replace('Cap', '').replace(':', '').lower()
                            cap_value = parts[1]
                            
                            # Check for dangerous capabilities
                            dangerous_caps_hex = {
                                '0000000000200000': 'CAP_SYS_ADMIN',  # Simplified check
                                '0000000000080000': 'CAP_SYS_PTRACE',
                                '0000000000010000': 'CAP_SYS_MODULE'
                            }
                            
                            if cap_value in dangerous_caps_hex:
                                self._create_security_alert(
                                    alert_type='dangerous_capability',
                                    severity='HIGH',
                                    description=f'Dangerous capability detected: {dangerous_caps_hex[cap_value]}',
                                    source='capability_monitor',
                                    metadata={
                                        'capability_type': cap_type,
                                        'capability_value': cap_value,
                                        'capability_name': dangerous_caps_hex[cap_value]
                                    }
                                )
        
        except (FileNotFoundError, IOError):
            pass
        except Exception as e:
            self.logger.debug(f"Error monitoring capabilities: {e}")
    
    def _detect_container_escape_attempts(self) -> None:
        """Detect potential container escape attempts"""
        try:
            escape_indicators = [
                # Check for access to host filesystem
                {'path': '/host', 'description': 'Host filesystem mount detected'},
                {'path': '/var/run/docker.sock', 'description': 'Docker socket access detected'},
                
                # Check for privileged device access
                {'path': '/dev/mem', 'description': 'Physical memory device access'},
                {'path': '/dev/kmem', 'description': 'Kernel memory device access'},
                {'path': '/dev/disk', 'description': 'Direct disk device access'},
            ]
            
            for indicator in escape_indicators:
                # Skip whitelisted paths
                if self._is_path_whitelisted(indicator['path']):
                    continue
                
                if Path(indicator['path']).exists():
                    # Check if we can access it (indicates potential escape)
                    try:
                        Path(indicator['path']).stat()
                        self._create_security_alert(
                            alert_type='container_escape_attempt',
                            severity='CRITICAL',
                            description=indicator['description'],
                            source='escape_detector',
                            metadata={
                                'indicator_path': indicator['path'],
                                'access_time': time.time()
                            }
                        )
                    except (PermissionError, FileNotFoundError):
                        # Good - we can't access it
                        pass
            
            # Better check: Detect if we're in host PID namespace (real escape indicator)
            # In a normal container, PID 1 is the container's init process
            # In host PID namespace or after escape, PID 1 is the host's init
            # Skip this check in Kubernetes mode as it causes false positives
            if not self.kubernetes_mode:
                try:
                    # Read PID 1's command line
                    with open('/proc/1/cmdline', 'r') as f:
                        pid1_cmd = f.read().replace('\x00', ' ').strip()
                    
                    # Host init processes (systemd, init, etc.)
                    host_init_indicators = ['/sbin/init', 'systemd', '/lib/systemd/systemd']
                    
                    # Check if PID 1 is a host init process
                    if any(indicator in pid1_cmd for indicator in host_init_indicators):
                        self._create_security_alert(
                            alert_type='container_escape_attempt',
                            severity='CRITICAL',
                            description='Host PID namespace detected - potential container escape',
                            source='escape_detector',
                            metadata={
                                'pid1_command': pid1_cmd,
                                'access_time': time.time()
                            }
                        )
                except (PermissionError, FileNotFoundError, OSError):
                    pass
        
        except Exception as e:
            self.logger.debug(f"Error detecting container escape attempts: {e}")
    
    def _create_security_alert(self, alert_type: str, severity: str, 
                             description: str, source: str, metadata: Dict[str, Any]) -> None:
        """Create and process a security alert"""
        alert = SecurityAlert(
            timestamp=time.time(),
            alert_type=alert_type,
            severity=severity,
            description=description,
            source=source,
            metadata=metadata
        )
        
        # Call alert callback if provided
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
        
        # Log the alert
        self.logger.warning(f"Security Alert [{alert_type}]: {description}")
    
    def get_security_events(self) -> List[RuntimeSecurityEvent]:
        """Get collected security events"""
        return self._security_events.copy()
    
    def clear_security_events(self) -> None:
        """Clear collected security events"""
        self._security_events.clear()
    
    def _is_path_whitelisted(self, path: str) -> bool:
        """Check if a path is whitelisted"""
        # Check exact match
        if path in self.allowed_mounts:
            return True
        
        # Check if path starts with any whitelisted mount
        for allowed_mount in self.allowed_mounts:
            if path.startswith(allowed_mount):
                return True
        
        return False
    
    def _is_fs_type_whitelisted(self, fs_type: str) -> bool:
        """Check if a filesystem type is whitelisted"""
        return fs_type in self.allowed_fs_types
    
    def _is_device_whitelisted(self, device: str) -> bool:
        """Check if a device is whitelisted"""
        return device in self.allowed_devices


class PolicyViolationDetector:
    """Detector for security policy violations"""
    
    def __init__(self):
        """Initialize policy violation detector"""
        self.logger = logging.getLogger(__name__)
        self.violation_rules = self._load_violation_rules()
    
    def _load_violation_rules(self) -> Dict[str, Any]:
        """Load security policy violation rules"""
        return {
            'pod_security_standards': {
                'restricted': {
                    'allowed_capabilities': ['CAP_NET_BIND_SERVICE'],
                    'forbidden_capabilities': ['CAP_SYS_ADMIN', 'CAP_SYS_PTRACE'],
                    'require_non_root': True,
                    'require_readonly_root': True,
                    'forbid_privilege_escalation': True
                },
                'baseline': {
                    'forbidden_capabilities': ['CAP_SYS_ADMIN'],
                    'forbid_host_network': True,
                    'forbid_host_pid': True,
                    'forbid_host_ipc': True
                }
            },
            'network_policies': {
                'require_network_policy': True,
                'forbid_default_allow': True
            },
            'rbac_policies': {
                'forbid_wildcard_permissions': True,
                'require_least_privilege': True
            }
        }
    
    def detect_violations(self, security_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect security policy violations"""
        violations = []
        
        # Check Pod Security Standards violations
        pss_violations = self._check_pod_security_standards(security_context)
        violations.extend(pss_violations)
        
        # Check capability violations
        capability_violations = self._check_capability_violations(security_context)
        violations.extend(capability_violations)
        
        # Check privilege violations
        privilege_violations = self._check_privilege_violations(security_context)
        violations.extend(privilege_violations)
        
        return violations
    
    def _check_pod_security_standards(self, security_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check Pod Security Standards compliance"""
        violations = []
        
        # Check restricted profile compliance
        restricted_rules = self.violation_rules['pod_security_standards']['restricted']
        
        # Check root user
        if security_context.get('user_id') == 0 and restricted_rules['require_non_root']:
            violations.append({
                'type': 'pod_security_standards',
                'policy': 'restricted',
                'violation': 'running_as_root',
                'description': 'Container running as root user violates restricted profile',
                'severity': 'HIGH'
            })
        
        # Check capabilities
        capabilities = security_context.get('capabilities', {})
        effective_caps = capabilities.get('effective', [])
        
        for cap in effective_caps:
            if cap in restricted_rules['forbidden_capabilities']:
                violations.append({
                    'type': 'pod_security_standards',
                    'policy': 'restricted',
                    'violation': 'forbidden_capability',
                    'description': f'Capability {cap} violates restricted profile',
                    'capability': cap,
                    'severity': 'HIGH'
                })
        
        return violations
    
    def _check_capability_violations(self, security_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for dangerous capability violations"""
        violations = []
        
        capabilities = security_context.get('capabilities', {})
        
        # Check all capability types
        for cap_type, cap_list in capabilities.items():
            for cap in cap_list:
                if cap in ['CAP_SYS_ADMIN', 'CAP_SYS_PTRACE', 'CAP_SYS_MODULE']:
                    violations.append({
                        'type': 'capability_violation',
                        'violation': 'dangerous_capability',
                        'description': f'Dangerous capability {cap} in {cap_type}',
                        'capability': cap,
                        'capability_type': cap_type,
                        'severity': 'HIGH'
                    })
        
        return violations
    
    def _check_privilege_violations(self, security_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for privilege escalation violations"""
        violations = []
        
        # Check for root filesystem write access
        if not security_context.get('root_filesystem_readonly', False):
            violations.append({
                'type': 'privilege_violation',
                'violation': 'writable_root_filesystem',
                'description': 'Root filesystem is writable',
                'severity': 'MEDIUM'
            })
        
        return violations