"""
Data models for Kubernetes metadata collection
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class KubernetesMetadata:
    """Kubernetes metadata structure"""
    pod_name: str = ""
    namespace: str = "default"
    node_name: str = ""
    cluster_name: str = ""
    deployment_name: str = ""
    service_name: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, str] = field(default_factory=dict)
    service_account: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'pod_name': self.pod_name,
            'namespace': self.namespace,
            'node_name': self.node_name,
            'cluster_name': self.cluster_name,
            'deployment_name': self.deployment_name,
            'service_name': self.service_name,
            'labels': self.labels,
            'annotations': self.annotations,
            'resource_limits': self.resource_limits,
            'service_account': self.service_account
        }


@dataclass
class SecurityContext:
    """Container security context information"""
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    run_as_non_root: Optional[bool] = None
    read_only_root_filesystem: Optional[bool] = None
    allow_privilege_escalation: Optional[bool] = None
    capabilities: Dict[str, List[str]] = field(default_factory=dict)
    security_policies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'group_id': self.group_id,
            'run_as_non_root': self.run_as_non_root,
            'read_only_root_filesystem': self.read_only_root_filesystem,
            'allow_privilege_escalation': self.allow_privilege_escalation,
            'capabilities': self.capabilities,
            'security_policies': self.security_policies
        }