"""
Enhanced security context detection and logging implementation
"""

import re
import os
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from .interfaces import ISecurityContextLogger
from .models import SecurityContext
from .advanced_monitor import RuntimeSecurityMonitor, PolicyViolationDetector, SecurityAlert
from .redaction_engine import AdvancedRedactionEngine, RedactionLevel, ConfigurationAuditor


class EnhancedSecurityContextLogger(ISecurityContextLogger):
    """Enhanced security context logger with comprehensive security monitoring"""
    
    def __init__(self, enable_runtime_monitoring: bool = True, enable_policy_detection: bool = True,
                 redaction_level: RedactionLevel = RedactionLevel.STRICT):
        """
        Initialize enhanced security context logger
        
        Args:
            enable_runtime_monitoring: Enable container runtime security event monitoring
            enable_policy_detection: Enable security policy and constraint detection
            redaction_level: Level of sensitive data redaction
        """
        self.enable_runtime_monitoring = enable_runtime_monitoring
        self.enable_policy_detection = enable_policy_detection
        self.logger = logging.getLogger(__name__)
        
        # Initialize advanced components
        self.redaction_engine = AdvancedRedactionEngine(redaction_level)
        self.config_auditor = ConfigurationAuditor()
        self.policy_detector = PolicyViolationDetector()
        
        # Initialize runtime security monitor with alert callback
        self.runtime_monitor: Optional[RuntimeSecurityMonitor] = None
        if self.enable_runtime_monitoring:
            self.runtime_monitor = RuntimeSecurityMonitor(
                alert_callback=self._handle_security_alert
            )
        
        # Enhanced patterns for sensitive data detection (kept for backward compatibility)
        self.sensitive_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
            'aws_access_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
            'aws_secret_key': re.compile(r'\b[A-Za-z0-9/+=]{40}\b'),
            'jwt_token': re.compile(r'\beyJ[A-Za-z0-9_/+=]+\.[A-Za-z0-9_/+=]+\.[A-Za-z0-9_/+=]*\b'),
            'api_key': re.compile(r'\b[Aa]pi[_-]?[Kk]ey[:\s]*[\'"]?([A-Za-z0-9_\-]{20,})[\'"]?\b'),
            'password': re.compile(r'\b[Pp]assword[:\s]*[\'"]?([A-Za-z0-9_\-@#$%^&*!]{8,})[\'"]?\b'),
            'private_key': re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----'),
            'certificate': re.compile(r'-----BEGIN CERTIFICATE-----')
        }
        
        # Kubernetes client for policy detection
        self._k8s_client: Optional[client.CoreV1Api] = None
        self._policy_client: Optional[client.PolicyV1Api] = None
        self._rbac_client: Optional[client.RbacAuthorizationV1Api] = None
        
        # Security event tracking
        self._security_events: List[Dict[str, Any]] = []
        self._audit_trail: List[Dict[str, Any]] = []
        
        # Pod and namespace information
        self._pod_name = os.getenv('HOSTNAME', '')
        self._namespace = self._get_namespace()
        
        # Initialize Kubernetes clients if policy detection is enabled
        if self.enable_policy_detection:
            self._initialize_k8s_clients()
        
        # Initialize runtime monitoring
        if self.enable_runtime_monitoring:
            self._initialize_runtime_monitoring()
            
        # Start runtime monitoring if available
        if self.runtime_monitor:
            self.runtime_monitor.start_monitoring()
    
    def _get_namespace(self) -> str:
        """Get the current namespace"""
        namespace = os.getenv('KUBERNETES_NAMESPACE')
        if namespace:
            return namespace
        
        try:
            with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, IOError):
            return 'default'
    
    def _initialize_k8s_clients(self) -> None:
        """Initialize Kubernetes API clients for policy detection"""
        try:
            if self._is_kubernetes_environment():
                config.load_incluster_config()
            else:
                config.load_kube_config()
            
            self._k8s_client = client.CoreV1Api()
            self._policy_client = client.PolicyV1Api()
            self._rbac_client = client.RbacAuthorizationV1Api()
            
            self.logger.info("Initialized Kubernetes clients for security policy detection")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize Kubernetes clients: {e}")
            self._k8s_client = None
            self._policy_client = None
            self._rbac_client = None
    
    def _initialize_runtime_monitoring(self) -> None:
        """Initialize container runtime security event monitoring"""
        try:
            # Check for available security monitoring tools
            self._runtime_tools = self._detect_runtime_security_tools()
            
            if self._runtime_tools:
                self.logger.info(f"Detected runtime security tools: {', '.join(self._runtime_tools)}")
            else:
                self.logger.info("No runtime security tools detected, using basic monitoring")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize runtime monitoring: {e}")
    
    def _handle_security_alert(self, alert: SecurityAlert) -> None:
        """Handle security alerts from runtime monitor"""
        # Convert alert to security event
        event_details = {
            'alert_type': alert.alert_type,
            'source': alert.source,
            'metadata': alert.metadata
        }
        
        # Log as security event
        self.log_security_event(alert.alert_type, event_details)
    
    def _detect_runtime_security_tools(self) -> List[str]:
        """Detect available container runtime security tools"""
        tools = []
        
        # Check for common security tools
        tool_checks = {
            'falco': ['/usr/bin/falco', '/bin/falco'],
            'sysdig': ['/usr/bin/sysdig', '/bin/sysdig'],
            'auditd': ['/sbin/auditd', '/usr/sbin/auditd'],
            'apparmor': ['/sys/kernel/security/apparmor'],
            'selinux': ['/sys/fs/selinux']
        }
        
        for tool, paths in tool_checks.items():
            for path in paths:
                if Path(path).exists():
                    tools.append(tool)
                    break
        
        return tools
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a comprehensive security-related event"""
        timestamp = time.time()
        
        # Enhanced security event with comprehensive context
        security_event = {
            'timestamp': timestamp,
            'iso_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
            'event_type': event_type,
            'severity': self._determine_event_severity(event_type, details),
            'details': details,
            'security_context': self.get_container_security_context(),
            'pod_name': self._pod_name,
            'namespace': self._namespace,
            'node_name': os.getenv('KUBERNETES_NODE_NAME', 'unknown'),
            'container_id': self._get_container_id(),
            'process_info': self._get_process_security_info(),
            'network_context': self._get_network_security_context(),
            'file_system_context': self._get_filesystem_security_context()
        }
        
        # Add runtime security context if available
        if self.enable_runtime_monitoring:
            security_event['runtime_security'] = self._get_runtime_security_context()
        
        # Add policy violations if detected
        if self.enable_policy_detection:
            security_event['policy_violations'] = self.validate_security_policies()
        
        # Store event for analysis
        self._security_events.append(security_event)
        
        # Log the event (this would integrate with the main logging system)
        self.logger.warning(f"Security Event [{event_type}]: {json.dumps(security_event, indent=2)}")
    
    def _determine_event_severity(self, event_type: str, details: Dict[str, Any]) -> str:
        """Determine the severity level of a security event"""
        high_severity_events = {
            'privilege_escalation', 'root_access', 'capability_added', 
            'sensitive_file_access', 'network_policy_violation',
            'unauthorized_api_access', 'container_escape_attempt'
        }
        
        medium_severity_events = {
            'policy_violation', 'configuration_change', 'unusual_process',
            'network_connection', 'file_permission_change'
        }
        
        if event_type in high_severity_events:
            return 'HIGH'
        elif event_type in medium_severity_events:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def redact_sensitive_data(self, message: str) -> str:
        """Enhanced redaction of sensitive data from log messages"""
        # Use the advanced redaction engine
        context = {
            'pod_name': self._pod_name,
            'namespace': self._namespace,
            'timestamp': time.time()
        }
        
        return self.redaction_engine.redact_message(message, context)
    
    def _apply_contextual_redaction(self, message: str) -> str:
        """Apply contextual redaction based on message content"""
        # Redact environment variables that might contain secrets
        env_pattern = re.compile(r'([A-Z_]+)=([^\s]+)')
        
        def redact_env_var(match):
            var_name, var_value = match.groups()
            if self._is_sensitive_env_var(var_name):
                return f"{var_name}=[REDACTED]"
            return match.group(0)
        
        return env_pattern.sub(redact_env_var, message)
    
    def _is_sensitive_env_var(self, name: str) -> bool:
        """Check if environment variable name indicates sensitive data"""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential', 
            'auth', 'cert', 'private', 'api_key', 'access_key',
            'database_url', 'connection_string', 'dsn'
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in sensitive_patterns)
    
    def get_container_security_context(self) -> Dict[str, Any]:
        """Get comprehensive container security context"""
        context = {
            # Basic process information
            'user_id': os.getuid() if hasattr(os, 'getuid') else None,
            'group_id': os.getgid() if hasattr(os, 'getgid') else None,
            'effective_user_id': os.geteuid() if hasattr(os, 'geteuid') else None,
            'effective_group_id': os.getegid() if hasattr(os, 'getegid') else None,
            
            # Extended security context
            'process_id': os.getpid(),
            'parent_process_id': os.getppid() if hasattr(os, 'getppid') else None,
            'session_id': os.getsid(0) if hasattr(os, 'getsid') else None,
            'umask': oct(os.umask(os.umask(0o022))),  # Get and restore umask
            
            # Container runtime information
            'container_id': self._get_container_id(),
            'container_runtime': self._detect_container_runtime(),
            
            # Security features
            'capabilities': self._get_process_capabilities(),
            'selinux_context': self._get_selinux_context(),
            'apparmor_profile': self._get_apparmor_profile(),
            'seccomp_mode': self._get_seccomp_mode(),
            
            # File system security
            'root_filesystem_readonly': self._is_root_filesystem_readonly(),
            'mount_namespace': self._get_mount_namespace(),
            
            # Network security
            'network_namespace': self._get_network_namespace(),
            'network_policies': self._get_network_policies() if self.enable_policy_detection else []
        }
        
        # Add Kubernetes security context if available
        if self._k8s_client and self._pod_name:
            k8s_security_context = self._get_kubernetes_security_context()
            context.update(k8s_security_context)
        
        return context
    
    def _get_container_id(self) -> str:
        """Get the current container ID"""
        try:
            # Try to read from cgroup
            with open('/proc/self/cgroup', 'r') as f:
                for line in f:
                    if 'docker' in line or 'containerd' in line:
                        # Extract container ID from cgroup path
                        parts = line.strip().split('/')
                        if len(parts) > 2:
                            container_id = parts[-1]
                            if len(container_id) >= 12:  # Docker container IDs are at least 12 chars
                                return container_id[:12]  # Return short form
            
            # Try hostname as fallback (often set to container ID)
            hostname = os.getenv('HOSTNAME', '')
            if len(hostname) >= 12:
                return hostname[:12]
                
        except (FileNotFoundError, IOError):
            pass
        
        return 'unknown'
    
    def _detect_container_runtime(self) -> str:
        """Detect the container runtime being used"""
        try:
            # Check for Docker
            if Path('/.dockerenv').exists():
                return 'docker'
            
            # Check for containerd
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'containerd' in content:
                    return 'containerd'
                elif 'docker' in content:
                    return 'docker'
                elif 'crio' in content:
                    return 'cri-o'
        
        except (FileNotFoundError, IOError):
            pass
        
        return 'unknown'
    
    def _get_process_capabilities(self) -> Dict[str, Any]:
        """Get process capabilities information"""
        capabilities = {
            'effective': [],
            'permitted': [],
            'inheritable': [],
            'bounding': [],
            'ambient': []
        }
        
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('Cap'):
                        parts = line.strip().split('\t')
                        if len(parts) == 2:
                            cap_type = parts[0].replace('Cap', '').replace(':', '').lower()
                            cap_value = parts[1]
                            
                            if cap_type in capabilities:
                                # Convert hex to capability names (simplified)
                                capabilities[cap_type] = self._parse_capabilities(cap_value)
        
        except (FileNotFoundError, IOError):
            pass
        
        return capabilities
    
    def _parse_capabilities(self, cap_hex: str) -> List[str]:
        """Parse capability hex value to capability names (simplified)"""
        # This is a simplified implementation
        # In production, you'd want a complete capability mapping
        cap_names = []
        
        try:
            cap_int = int(cap_hex, 16)
            
            # Common capabilities (bit positions)
            capability_map = {
                0: 'CAP_CHOWN',
                1: 'CAP_DAC_OVERRIDE',
                2: 'CAP_DAC_READ_SEARCH',
                3: 'CAP_FOWNER',
                4: 'CAP_FSETID',
                5: 'CAP_KILL',
                6: 'CAP_SETGID',
                7: 'CAP_SETUID',
                8: 'CAP_SETPCAP',
                9: 'CAP_LINUX_IMMUTABLE',
                10: 'CAP_NET_BIND_SERVICE',
                11: 'CAP_NET_BROADCAST',
                12: 'CAP_NET_ADMIN',
                13: 'CAP_NET_RAW',
                14: 'CAP_IPC_LOCK',
                15: 'CAP_IPC_OWNER',
                16: 'CAP_SYS_MODULE',
                17: 'CAP_SYS_RAWIO',
                18: 'CAP_SYS_CHROOT',
                19: 'CAP_SYS_PTRACE',
                20: 'CAP_SYS_PACCT',
                21: 'CAP_SYS_ADMIN',
                22: 'CAP_SYS_BOOT',
                23: 'CAP_SYS_NICE',
                24: 'CAP_SYS_RESOURCE',
                25: 'CAP_SYS_TIME',
                26: 'CAP_SYS_TTY_CONFIG',
                27: 'CAP_MKNOD',
                28: 'CAP_LEASE',
                29: 'CAP_AUDIT_WRITE',
                30: 'CAP_AUDIT_CONTROL',
                31: 'CAP_SETFCAP'
            }
            
            for bit, cap_name in capability_map.items():
                if cap_int & (1 << bit):
                    cap_names.append(cap_name)
        
        except ValueError:
            pass
        
        return cap_names
    
    def _get_selinux_context(self) -> Optional[str]:
        """Get SELinux security context"""
        try:
            with open('/proc/self/attr/current', 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, IOError):
            return None
    
    def _get_apparmor_profile(self) -> Optional[str]:
        """Get AppArmor profile information"""
        try:
            with open('/proc/self/attr/apparmor/current', 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, IOError):
            # Try alternative path
            try:
                with open('/proc/self/attr/current', 'r') as f:
                    content = f.read().strip()
                    if content and content != 'unconfined':
                        return content
            except (FileNotFoundError, IOError):
                pass
            return None
    
    def _get_seccomp_mode(self) -> Optional[str]:
        """Get seccomp mode information"""
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('Seccomp:'):
                        mode_num = line.split('\t')[1].strip()
                        mode_map = {
                            '0': 'disabled',
                            '1': 'strict',
                            '2': 'filter'
                        }
                        return mode_map.get(mode_num, f'unknown({mode_num})')
        except (FileNotFoundError, IOError):
            pass
        return None
    
    def _is_root_filesystem_readonly(self) -> bool:
        """Check if root filesystem is mounted read-only"""
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[1] == '/':
                        mount_options = parts[3].split(',')
                        return 'ro' in mount_options
        except (FileNotFoundError, IOError):
            pass
        return False
    
    def _get_mount_namespace(self) -> Optional[str]:
        """Get mount namespace ID"""
        try:
            ns_path = Path('/proc/self/ns/mnt')
            if ns_path.exists():
                link_target = str(ns_path.readlink())
                return link_target.split('[')[1].split(']')[0]
        except (FileNotFoundError, IOError, IndexError):
            pass
        return None
    
    def _get_network_namespace(self) -> Optional[str]:
        """Get network namespace ID"""
        try:
            ns_path = Path('/proc/self/ns/net')
            if ns_path.exists():
                link_target = str(ns_path.readlink())
                return link_target.split('[')[1].split(']')[0]
        except (FileNotFoundError, IOError, IndexError):
            pass
        return None
    
    def _get_process_security_info(self) -> Dict[str, Any]:
        """Get detailed process security information"""
        return {
            'command_line': self._get_process_cmdline(),
            'environment_variables': self._get_filtered_env_vars(),
            'open_files': self._get_open_files_count(),
            'network_connections': self._get_network_connections_count(),
            'memory_maps': self._get_memory_maps_info()
        }
    
    def _get_process_cmdline(self) -> str:
        """Get process command line"""
        try:
            with open('/proc/self/cmdline', 'rb') as f:
                cmdline = f.read().decode('utf-8', errors='ignore')
                return cmdline.replace('\x00', ' ').strip()
        except (FileNotFoundError, IOError):
            return 'unknown'
    
    def _get_filtered_env_vars(self) -> Dict[str, str]:
        """Get filtered environment variables (excluding sensitive ones)"""
        filtered_env = {}
        
        for key, value in os.environ.items():
            if not self._is_sensitive_env_var(key):
                filtered_env[key] = value
            else:
                filtered_env[key] = '[REDACTED]'
        
        return filtered_env
    
    def _get_open_files_count(self) -> int:
        """Get count of open file descriptors"""
        try:
            fd_dir = Path('/proc/self/fd')
            return len(list(fd_dir.iterdir()))
        except (FileNotFoundError, IOError):
            return 0
    
    def _get_network_connections_count(self) -> int:
        """Get count of network connections"""
        try:
            with open('/proc/net/tcp', 'r') as f:
                return len(f.readlines()) - 1  # Subtract header line
        except (FileNotFoundError, IOError):
            return 0
    
    def _get_memory_maps_info(self) -> Dict[str, Any]:
        """Get memory mapping information"""
        try:
            with open('/proc/self/maps', 'r') as f:
                lines = f.readlines()
                
            executable_maps = 0
            writable_maps = 0
            total_maps = len(lines)
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    permissions = parts[1]
                    if 'x' in permissions:
                        executable_maps += 1
                    if 'w' in permissions:
                        writable_maps += 1
            
            return {
                'total_maps': total_maps,
                'executable_maps': executable_maps,
                'writable_maps': writable_maps
            }
        
        except (FileNotFoundError, IOError):
            return {'total_maps': 0, 'executable_maps': 0, 'writable_maps': 0}
    
    def _get_network_security_context(self) -> Dict[str, Any]:
        """Get network security context"""
        return {
            'listening_ports': self._get_listening_ports(),
            'network_interfaces': self._get_network_interfaces(),
            'iptables_rules': self._get_iptables_rules_count()
        }
    
    def _get_listening_ports(self) -> List[int]:
        """Get list of listening ports"""
        ports = []
        
        try:
            # Check TCP ports
            with open('/proc/net/tcp', 'r') as f:
                for line in f.readlines()[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 4 and parts[3] == '0A':  # LISTEN state
                        local_address = parts[1]
                        port = int(local_address.split(':')[1], 16)
                        ports.append(port)
        
        except (FileNotFoundError, IOError):
            pass
        
        return sorted(list(set(ports)))
    
    def _get_network_interfaces(self) -> List[str]:
        """Get list of network interfaces"""
        interfaces = []
        
        try:
            net_dir = Path('/sys/class/net')
            if net_dir.exists():
                interfaces = [iface.name for iface in net_dir.iterdir() if iface.is_dir()]
        
        except (FileNotFoundError, IOError):
            pass
        
        return interfaces
    
    def _get_iptables_rules_count(self) -> int:
        """Get count of iptables rules (if accessible)"""
        try:
            result = subprocess.run(['iptables', '-L', '-n'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return len(result.stdout.splitlines())
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return 0
    
    def _get_filesystem_security_context(self) -> Dict[str, Any]:
        """Get filesystem security context"""
        return {
            'mount_points': self._get_mount_points(),
            'file_permissions': self._check_critical_file_permissions(),
            'disk_usage': self._get_disk_usage()
        }
    
    def _get_mount_points(self) -> List[Dict[str, str]]:
        """Get filesystem mount points"""
        mounts = []
        
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4:
                        mounts.append({
                            'device': parts[0],
                            'mount_point': parts[1],
                            'filesystem_type': parts[2],
                            'options': parts[3]
                        })
        
        except (FileNotFoundError, IOError):
            pass
        
        return mounts
    
    def _check_critical_file_permissions(self) -> Dict[str, str]:
        """Check permissions on critical files"""
        critical_files = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/group',
            '/etc/sudoers',
            '/root/.ssh/authorized_keys'
        ]
        
        permissions = {}
        
        for file_path in critical_files:
            try:
                path = Path(file_path)
                if path.exists():
                    stat = path.stat()
                    permissions[file_path] = oct(stat.st_mode)[-3:]
            except (FileNotFoundError, PermissionError):
                permissions[file_path] = 'inaccessible'
        
        return permissions
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            
            return {
                'total_bytes': total,
                'used_bytes': used,
                'free_bytes': free,
                'usage_percentage': round((used / total) * 100, 2) if total > 0 else 0
            }
        
        except Exception:
            return {'total_bytes': 0, 'used_bytes': 0, 'free_bytes': 0, 'usage_percentage': 0}
    
    def _get_kubernetes_security_context(self) -> Dict[str, Any]:
        """Get Kubernetes-specific security context"""
        if not self._k8s_client or not self._pod_name:
            return {}
        
        try:
            pod = self._k8s_client.read_namespaced_pod(
                name=self._pod_name,
                namespace=self._namespace
            )
            
            k8s_context = {}
            
            # Pod security context
            if pod.spec.security_context:
                pod_sc = pod.spec.security_context
                k8s_context['pod_security_context'] = {
                    'run_as_user': pod_sc.run_as_user,
                    'run_as_group': pod_sc.run_as_group,
                    'run_as_non_root': pod_sc.run_as_non_root,
                    'fs_group': pod_sc.fs_group,
                    'supplemental_groups': pod_sc.supplemental_groups or [],
                    'seccomp_profile': pod_sc.seccomp_profile.type if pod_sc.seccomp_profile else None,
                    'se_linux_options': {
                        'level': pod_sc.se_linux_options.level if pod_sc.se_linux_options else None,
                        'role': pod_sc.se_linux_options.role if pod_sc.se_linux_options else None,
                        'type': pod_sc.se_linux_options.type if pod_sc.se_linux_options else None,
                        'user': pod_sc.se_linux_options.user if pod_sc.se_linux_options else None
                    } if pod_sc.se_linux_options else None
                }
            
            # Container security contexts
            if pod.spec.containers:
                container_contexts = []
                for container in pod.spec.containers:
                    if container.security_context:
                        container_sc = container.security_context
                        container_contexts.append({
                            'name': container.name,
                            'run_as_user': container_sc.run_as_user,
                            'run_as_group': container_sc.run_as_group,
                            'run_as_non_root': container_sc.run_as_non_root,
                            'read_only_root_filesystem': container_sc.read_only_root_filesystem,
                            'allow_privilege_escalation': container_sc.allow_privilege_escalation,
                            'privileged': container_sc.privileged,
                            'capabilities': {
                                'add': list(container_sc.capabilities.add) if container_sc.capabilities and container_sc.capabilities.add else [],
                                'drop': list(container_sc.capabilities.drop) if container_sc.capabilities and container_sc.capabilities.drop else []
                            } if container_sc.capabilities else {'add': [], 'drop': []}
                        })
                
                k8s_context['container_security_contexts'] = container_contexts
            
            return k8s_context
        
        except Exception as e:
            self.logger.debug(f"Failed to get Kubernetes security context: {e}")
            return {}
    
    def _get_runtime_security_context(self) -> Dict[str, Any]:
        """Get container runtime security context"""
        runtime_context = {
            'detected_tools': self._runtime_tools,
            'security_events': len(self._security_events),
            'runtime_violations': []
        }
        
        # Check for common runtime security violations
        violations = []
        
        # Check for privileged execution
        if os.getuid() == 0:
            violations.append({
                'type': 'privileged_execution',
                'description': 'Container running as root user',
                'severity': 'HIGH'
            })
        
        # Check for dangerous capabilities
        capabilities = self._get_process_capabilities()
        dangerous_caps = ['CAP_SYS_ADMIN', 'CAP_SYS_PTRACE', 'CAP_SYS_MODULE', 'CAP_DAC_OVERRIDE']
        
        for cap_type, cap_list in capabilities.items():
            for dangerous_cap in dangerous_caps:
                if dangerous_cap in cap_list:
                    violations.append({
                        'type': 'dangerous_capability',
                        'description': f'Container has dangerous capability: {dangerous_cap}',
                        'capability': dangerous_cap,
                        'capability_type': cap_type,
                        'severity': 'HIGH'
                    })
        
        # Check for writable root filesystem
        if not self._is_root_filesystem_readonly():
            violations.append({
                'type': 'writable_root_filesystem',
                'description': 'Root filesystem is writable',
                'severity': 'MEDIUM'
            })
        
        runtime_context['runtime_violations'] = violations
        
        return runtime_context
    
    def _get_network_policies(self) -> List[Dict[str, Any]]:
        """Get network policies affecting this pod"""
        if not self._k8s_client:
            return []
        
        try:
            networking_client = client.NetworkingV1Api()
            network_policies = networking_client.list_namespaced_network_policy(
                namespace=self._namespace
            )
            
            policies = []
            for policy in network_policies.items:
                policies.append({
                    'name': policy.metadata.name,
                    'namespace': policy.metadata.namespace,
                    'pod_selector': policy.spec.pod_selector.match_labels if policy.spec.pod_selector else {},
                    'policy_types': policy.spec.policy_types or [],
                    'ingress_rules': len(policy.spec.ingress) if policy.spec.ingress else 0,
                    'egress_rules': len(policy.spec.egress) if policy.spec.egress else 0
                })
            
            return policies
        
        except Exception as e:
            self.logger.debug(f"Failed to get network policies: {e}")
            return []
    
    def audit_configuration_change(self, component: str, old_config: Dict[str, Any], 
                                 new_config: Dict[str, Any]) -> None:
        """Enhanced audit logging for configuration changes"""
        timestamp = time.time()
        
        # Calculate configuration diff
        changes = self._calculate_config_diff(old_config, new_config)
        
        audit_entry = {
            'timestamp': timestamp,
            'iso_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
            'event_type': 'configuration_change',
            'component': component,
            'changes': changes,
            'change_count': len(changes),
            'security_impact': self._assess_security_impact(changes),
            'user_context': {
                'user_id': os.getuid() if hasattr(os, 'getuid') else None,
                'effective_user_id': os.geteuid() if hasattr(os, 'geteuid') else None,
                'process_id': os.getpid(),
                'command_line': self._get_process_cmdline()
            },
            'kubernetes_context': {
                'pod_name': self._pod_name,
                'namespace': self._namespace,
                'node_name': os.getenv('KUBERNETES_NODE_NAME', 'unknown')
            }
        }
        
        # Store audit entry
        self._audit_trail.append(audit_entry)
        
        # Use configuration auditor for detailed auditing
        user_context = audit_entry['user_context']
        for change in changes:
            self.config_auditor.audit_redaction_config_change(
                component=component,
                change_type=change['type'],
                old_value=change.get('old_value'),
                new_value=change.get('new_value'),
                user_context=user_context
            )
        
        # Log security-relevant configuration changes
        if audit_entry['security_impact'] in ['HIGH', 'MEDIUM']:
            self.log_security_event('configuration_change', audit_entry)
        
        self.logger.info(f"Configuration change audited for {component}: {len(changes)} changes")
    
    def _calculate_config_diff(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate differences between configuration objects"""
        changes = []
        
        # Find added keys
        for key in new_config:
            if key not in old_config:
                changes.append({
                    'type': 'added',
                    'key': key,
                    'new_value': new_config[key]
                })
        
        # Find removed keys
        for key in old_config:
            if key not in new_config:
                changes.append({
                    'type': 'removed',
                    'key': key,
                    'old_value': old_config[key]
                })
        
        # Find modified keys
        for key in old_config:
            if key in new_config and old_config[key] != new_config[key]:
                changes.append({
                    'type': 'modified',
                    'key': key,
                    'old_value': old_config[key],
                    'new_value': new_config[key]
                })
        
        return changes
    
    def _assess_security_impact(self, changes: List[Dict[str, Any]]) -> str:
        """Assess the security impact of configuration changes"""
        high_impact_keys = {
            'security_context', 'capabilities', 'privileged', 'run_as_user',
            'run_as_group', 'allow_privilege_escalation', 'read_only_root_filesystem',
            'network_policy', 'rbac', 'service_account', 'secrets', 'tls'
        }
        
        medium_impact_keys = {
            'environment', 'volumes', 'mounts', 'ports', 'resources',
            'image', 'command', 'args', 'labels', 'annotations'
        }
        
        for change in changes:
            key = change['key'].lower()
            
            # Check for high impact changes
            if any(impact_key in key for impact_key in high_impact_keys):
                return 'HIGH'
        
        for change in changes:
            key = change['key'].lower()
            
            # Check for medium impact changes
            if any(impact_key in key for impact_key in medium_impact_keys):
                return 'MEDIUM'
        
        return 'LOW'
    
    def validate_security_policies(self) -> List[str]:
        """Enhanced validation of security policies and constraints"""
        violations = []
        
        # Get current security context
        security_context = self.get_container_security_context()
        
        # Use policy detector for comprehensive violation detection
        policy_violations = self.policy_detector.detect_violations(security_context)
        
        # Convert policy violations to string format for backward compatibility
        for violation in policy_violations:
            violations.append(violation['description'])
        
        # Basic security checks (kept for backward compatibility)
        if hasattr(os, 'getuid') and os.getuid() == 0:
            violations.append("Container running as root user (UID 0)")
        
        # Check for dangerous capabilities
        capabilities = self._get_process_capabilities()
        dangerous_caps = ['CAP_SYS_ADMIN', 'CAP_SYS_PTRACE', 'CAP_SYS_MODULE']
        
        for cap_type, cap_list in capabilities.items():
            for dangerous_cap in dangerous_caps:
                if dangerous_cap in cap_list:
                    violations.append(f"Dangerous capability detected: {dangerous_cap} in {cap_type}")
        
        # Check filesystem security
        if not self._is_root_filesystem_readonly():
            violations.append("Root filesystem is writable")
        
        # Kubernetes-specific policy validation
        if self.enable_policy_detection and self._k8s_client:
            k8s_violations = self._validate_kubernetes_policies()
            violations.extend(k8s_violations)
        
        # Pod Security Standards validation
        if self.enable_policy_detection:
            pss_violations = self._validate_pod_security_standards()
            violations.extend(pss_violations)
        
        return violations
    
    def _validate_kubernetes_policies(self) -> List[str]:
        """Validate Kubernetes-specific security policies"""
        violations = []
        
        try:
            # Check Pod Security Policies (if available)
            if self._policy_client:
                try:
                    psps = self._policy_client.list_pod_security_policy()
                    if psps.items:
                        violations.extend(self._check_pod_security_policy_compliance(psps.items))
                except ApiException as e:
                    if e.status != 404:  # PSP might not be available in newer clusters
                        self.logger.debug(f"Failed to check Pod Security Policies: {e}")
            
            # Check Network Policies
            network_violations = self._check_network_policy_compliance()
            violations.extend(network_violations)
            
            # Check RBAC policies
            rbac_violations = self._check_rbac_compliance()
            violations.extend(rbac_violations)
        
        except Exception as e:
            self.logger.debug(f"Failed to validate Kubernetes policies: {e}")
        
        return violations
    
    def _validate_pod_security_standards(self) -> List[str]:
        """Validate against Pod Security Standards"""
        violations = []
        
        # Get current security context
        security_context = self.get_container_security_context()
        
        # Restricted profile checks
        if security_context.get('user_id') == 0:
            violations.append("Pod Security Standards: Running as root violates 'restricted' profile")
        
        if security_context.get('capabilities', {}).get('effective'):
            effective_caps = security_context['capabilities']['effective']
            allowed_caps = ['CAP_NET_BIND_SERVICE']  # Only this is allowed in restricted
            
            for cap in effective_caps:
                if cap not in allowed_caps:
                    violations.append(f"Pod Security Standards: Capability {cap} violates 'restricted' profile")
        
        # Check for privilege escalation
        k8s_context = self._get_kubernetes_security_context()
        container_contexts = k8s_context.get('container_security_contexts', [])
        
        for container_ctx in container_contexts:
            if container_ctx.get('allow_privilege_escalation', True):
                violations.append(f"Pod Security Standards: Container {container_ctx['name']} allows privilege escalation")
            
            if container_ctx.get('privileged', False):
                violations.append(f"Pod Security Standards: Container {container_ctx['name']} runs in privileged mode")
            
            if not container_ctx.get('read_only_root_filesystem', False):
                violations.append(f"Pod Security Standards: Container {container_ctx['name']} has writable root filesystem")
        
        return violations
    
    def _check_pod_security_policy_compliance(self, psps) -> List[str]:
        """Check compliance with Pod Security Policies"""
        violations = []
        
        # This is a simplified implementation
        # In production, you'd want comprehensive PSP validation
        
        for psp in psps:
            if hasattr(psp.spec, 'privileged') and psp.spec.privileged:
                violations.append(f"Pod Security Policy '{psp.metadata.name}' allows privileged containers")
            
            if hasattr(psp.spec, 'allow_privilege_escalation') and psp.spec.allow_privilege_escalation:
                violations.append(f"Pod Security Policy '{psp.metadata.name}' allows privilege escalation")
        
        return violations
    
    def _check_network_policy_compliance(self) -> List[str]:
        """Check network policy compliance"""
        violations = []
        
        try:
            networking_client = client.NetworkingV1Api()
            network_policies = networking_client.list_namespaced_network_policy(
                namespace=self._namespace
            )
            
            if not network_policies.items:
                violations.append("No network policies found in namespace - traffic not restricted")
            else:
                # Check for overly permissive policies
                for policy in network_policies.items:
                    if not policy.spec.ingress and not policy.spec.egress:
                        violations.append(f"Network policy '{policy.metadata.name}' has no ingress or egress rules")
        
        except Exception as e:
            self.logger.debug(f"Failed to check network policies: {e}")
        
        return violations
    
    def _check_rbac_compliance(self) -> List[str]:
        """Check RBAC compliance"""
        violations = []
        
        try:
            if not self._rbac_client:
                return violations
            
            # Check for overly permissive cluster roles
            cluster_roles = self._rbac_client.list_cluster_role()
            
            for role in cluster_roles.items:
                if role.rules:
                    for rule in role.rules:
                        if rule.verbs and '*' in rule.verbs:
                            violations.append(f"Cluster role '{role.metadata.name}' has wildcard verbs")
                        
                        if rule.resources and '*' in rule.resources:
                            violations.append(f"Cluster role '{role.metadata.name}' has wildcard resources")
        
        except Exception as e:
            self.logger.debug(f"Failed to check RBAC compliance: {e}")
        
        return violations
    
    def _is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes environment"""
        return os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    def get_security_events(self) -> List[Dict[str, Any]]:
        """Get all recorded security events"""
        return self._security_events.copy()
    
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get complete audit trail"""
        return self._audit_trail.copy()
    
    def clear_security_events(self) -> None:
        """Clear recorded security events"""
        self._security_events.clear()
    
    def clear_audit_trail(self) -> None:
        """Clear audit trail"""
        self._audit_trail.clear()
        self.config_auditor.clear_audit_trail()
    
    def get_redaction_statistics(self) -> Dict[str, Any]:
        """Get redaction engine statistics"""
        return self.redaction_engine.get_statistics()
    
    def get_redaction_audit_trail(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get redaction audit trail"""
        return self.redaction_engine.get_audit_trail(limit)
    
    def get_configuration_audit_trail(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get configuration change audit trail"""
        return self.config_auditor.get_audit_trail(limit)
    
    def add_custom_redaction_rule(self, name: str, pattern: str, replacement: str, 
                                 description: str, level: str = 'STRICT') -> None:
        """Add custom redaction rule"""
        redaction_level = RedactionLevel(level.lower())
        self.redaction_engine.add_custom_rule(name, pattern, replacement, description, redaction_level)
        
        # Audit the configuration change
        self.config_auditor.audit_redaction_config_change(
            component='redaction_engine',
            change_type='add_custom_rule',
            old_value=None,
            new_value={'name': name, 'pattern': pattern, 'replacement': replacement}
        )
    
    def remove_redaction_rule(self, name: str) -> bool:
        """Remove redaction rule"""
        success = self.redaction_engine.remove_rule(name)
        
        if success:
            # Audit the configuration change
            self.config_auditor.audit_redaction_config_change(
                component='redaction_engine',
                change_type='remove_rule',
                old_value=name,
                new_value=None
            )
        
        return success
    
    def get_runtime_security_events(self) -> List[Dict[str, Any]]:
        """Get runtime security events"""
        if self.runtime_monitor:
            events = self.runtime_monitor.get_security_events()
            return [event.to_dict() for event in events]
        return []
    
    def stop_runtime_monitoring(self) -> None:
        """Stop runtime security monitoring"""
        if self.runtime_monitor:
            self.runtime_monitor.stop_monitoring()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.stop_runtime_monitoring()
        except Exception:
            pass  # Ignore cleanup errors


# Maintain backward compatibility
class BaseSecurityContextLogger(EnhancedSecurityContextLogger):
    """Backward compatibility alias"""
    pass