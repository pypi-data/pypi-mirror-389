"""
Interfaces for Kubernetes metadata collection components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IMetadataCollector(ABC):
    """Interface for Kubernetes metadata collection"""
    
    @abstractmethod
    def collect_pod_metadata(self) -> Dict[str, Any]:
        """Collect current pod metadata from Kubernetes API"""
        pass
    
    @abstractmethod
    def collect_node_metadata(self) -> Dict[str, Any]:
        """Collect node metadata from Kubernetes API"""
        pass
    
    @abstractmethod
    def collect_deployment_metadata(self) -> Dict[str, Any]:
        """Collect deployment and service metadata"""
        pass
    
    @abstractmethod
    def get_security_context(self) -> Dict[str, Any]:
        """Get container security context information"""
        pass
    
    @abstractmethod
    def is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes environment"""
        pass
    
    @abstractmethod
    def refresh_metadata_cache(self) -> None:
        """Refresh cached metadata from Kubernetes API"""
        pass