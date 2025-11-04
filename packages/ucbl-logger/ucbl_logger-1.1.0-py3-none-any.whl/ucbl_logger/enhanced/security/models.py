"""
Enhanced data models for security logging
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class SecurityEventSeverity(Enum):
    """Security event severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityEventType(Enum):
    """Security event types"""
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ROOT_ACCESS = "root_access"
    CAPABILITY_ADDED = "capability_added"
    SENSITIVE_FILE_ACCESS = "sensitive_file_access"
    NETWORK_POLICY_VIOLATION = "network_policy_violation"
    UNAUTHORIZED_API_ACCESS = "unauthorized_api_access"
    CONTAINER_ESCAPE_ATTEMPT = "container_escape_attempt"
    POLICY_VIOLATION = "policy_violation"
    CONFIGURATION_CHANGE = "configuration_change"
    UNUSUAL_PROCESS = "unusual_process"
    NETWORK_CONNECTION = "network_connection"
    FILE_PERMISSION_CHANGE = "file_permission_change"


@dataclass
class SecurityContext:
    """Enhanced container security context information"""
    # Basic process information
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    effective_user_id: Optional[int] = None
    effective_group_id: Optional[int] = None
    
    # Kubernetes security context
    run_as_non_root: Optional[bool] = None
    read_only_root_filesystem: Optional[bool] = None
    allow_privilege_escalation: Optional[bool] = None
    privileged: Optional[bool] = None
    
    # Capabilities
    capabilities: Dict[str, List[str]] = field(default_factory=dict)
    
    # Security policies and constraints
    security_policies: List[str] = field(default_factory=list)
    pod_security_standards: Optional[str] = None
    
    # Container runtime information
    container_id: Optional[str] = None
    container_runtime: Optional[str] = None
    
    # Security features
    selinux_context: Optional[str] = None
    apparmor_profile: Optional[str] = None
    seccomp_mode: Optional[str] = None
    
    # Namespace information
    mount_namespace: Optional[str] = None
    network_namespace: Optional[str] = None
    
    # Additional security metadata
    security_violations: List[str] = field(default_factory=list)
    runtime_security_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'group_id': self.group_id,
            'effective_user_id': self.effective_user_id,
            'effective_group_id': self.effective_group_id,
            'run_as_non_root': self.run_as_non_root,
            'read_only_root_filesystem': self.read_only_root_filesystem,
            'allow_privilege_escalation': self.allow_privilege_escalation,
            'privileged': self.privileged,
            'capabilities': self.capabilities,
            'security_policies': self.security_policies,
            'pod_security_standards': self.pod_security_standards,
            'container_id': self.container_id,
            'container_runtime': self.container_runtime,
            'selinux_context': self.selinux_context,
            'apparmor_profile': self.apparmor_profile,
            'seccomp_mode': self.seccomp_mode,
            'mount_namespace': self.mount_namespace,
            'network_namespace': self.network_namespace,
            'security_violations': self.security_violations,
            'runtime_security_events': self.runtime_security_events
        }


@dataclass
class SecurityEvent:
    """Security event data model"""
    timestamp: float
    event_type: str
    severity: str
    details: Dict[str, Any]
    security_context: Dict[str, Any]
    pod_name: str
    namespace: str
    node_name: str
    container_id: str
    
    # Process information
    process_info: Dict[str, Any] = field(default_factory=dict)
    
    # Network context
    network_context: Dict[str, Any] = field(default_factory=dict)
    
    # File system context
    file_system_context: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime security context
    runtime_security: Dict[str, Any] = field(default_factory=dict)
    
    # Policy violations
    policy_violations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'severity': self.severity,
            'details': self.details,
            'security_context': self.security_context,
            'pod_name': self.pod_name,
            'namespace': self.namespace,
            'node_name': self.node_name,
            'container_id': self.container_id,
            'process_info': self.process_info,
            'network_context': self.network_context,
            'file_system_context': self.file_system_context,
            'runtime_security': self.runtime_security,
            'policy_violations': self.policy_violations
        }


@dataclass
class AuditEntry:
    """Audit trail entry for configuration changes"""
    timestamp: float
    event_type: str
    component: str
    changes: List[Dict[str, Any]]
    change_count: int
    security_impact: str
    user_context: Dict[str, Any]
    kubernetes_context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'component': self.component,
            'changes': self.changes,
            'change_count': self.change_count,
            'security_impact': self.security_impact,
            'user_context': self.user_context,
            'kubernetes_context': self.kubernetes_context
        }


@dataclass
class PolicyViolation:
    """Security policy violation information"""
    policy_type: str
    policy_name: str
    violation_type: str
    description: str
    severity: str
    remediation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'policy_type': self.policy_type,
            'policy_name': self.policy_name,
            'violation_type': self.violation_type,
            'description': self.description,
            'severity': self.severity,
            'remediation': self.remediation
        }


@dataclass
class RuntimeSecurityEvent:
    """Container runtime security event"""
    timestamp: float
    event_type: str
    source: str  # falco, sysdig, auditd, etc.
    severity: str
    description: str
    process_info: Dict[str, Any] = field(default_factory=dict)
    file_info: Dict[str, Any] = field(default_factory=dict)
    network_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'source': self.source,
            'severity': self.severity,
            'description': self.description,
            'process_info': self.process_info,
            'file_info': self.file_info,
            'network_info': self.network_info
        }