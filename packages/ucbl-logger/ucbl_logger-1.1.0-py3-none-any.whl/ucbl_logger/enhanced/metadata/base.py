"""
Base implementation for Kubernetes metadata collection components
"""

import os
from typing import Dict, Any
from .interfaces import IMetadataCollector


class BaseMetadataCollector(IMetadataCollector):
    """Base implementation of metadata collector"""
    
    def __init__(self):
        self.metadata_cache: Dict[str, Any] = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes
    
    def collect_pod_metadata(self) -> Dict[str, Any]:
        """Collect current pod metadata from Kubernetes API"""
        # Basic implementation using environment variables
        return {
            'pod_name': os.getenv('HOSTNAME', 'unknown'),
            'namespace': os.getenv('KUBERNETES_NAMESPACE', 'default'),
            'service_account': os.getenv('KUBERNETES_SERVICE_ACCOUNT', 'default')
        }
    
    def collect_node_metadata(self) -> Dict[str, Any]:
        """Collect node metadata from Kubernetes API"""
        return {
            'node_name': os.getenv('KUBERNETES_NODE_NAME', 'unknown'),
            'cluster_name': os.getenv('KUBERNETES_CLUSTER_NAME', 'unknown')
        }
    
    def collect_deployment_metadata(self) -> Dict[str, Any]:
        """Collect deployment and service metadata"""
        return {
            'deployment_name': os.getenv('KUBERNETES_DEPLOYMENT_NAME', 'unknown'),
            'service_name': os.getenv('KUBERNETES_SERVICE_NAME', 'unknown')
        }
    
    def get_security_context(self) -> Dict[str, Any]:
        """Get container security context information"""
        return {
            'user_id': os.getuid() if hasattr(os, 'getuid') else None,
            'group_id': os.getgid() if hasattr(os, 'getgid') else None
        }
    
    def is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes environment"""
        return os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    def refresh_metadata_cache(self) -> None:
        """Refresh cached metadata from Kubernetes API"""
        self.metadata_cache = {
            **self.collect_pod_metadata(),
            **self.collect_node_metadata(),
            **self.collect_deployment_metadata()
        }
        self.cache_timestamp = time.time()
        
import time