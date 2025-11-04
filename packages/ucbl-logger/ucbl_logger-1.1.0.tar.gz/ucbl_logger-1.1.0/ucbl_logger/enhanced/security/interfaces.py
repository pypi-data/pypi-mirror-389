"""
Interfaces for enhanced security logging components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ISecurityContextLogger(ABC):
    """Interface for enhanced security context logging and data protection"""
    
    @abstractmethod
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a comprehensive security-related event with full context"""
        pass
    
    @abstractmethod
    def redact_sensitive_data(self, message: str) -> str:
        """Enhanced redaction of sensitive data from log messages"""
        pass
    
    @abstractmethod
    def get_container_security_context(self) -> Dict[str, Any]:
        """Get comprehensive container security context including runtime info"""
        pass
    
    @abstractmethod
    def audit_configuration_change(self, component: str, old_config: Dict[str, Any], 
                                 new_config: Dict[str, Any]) -> None:
        """Enhanced audit logging for configuration changes with security impact assessment"""
        pass
    
    @abstractmethod
    def validate_security_policies(self) -> List[str]:
        """Enhanced validation of security policies including Pod Security Standards"""
        pass
    
    @abstractmethod
    def get_security_events(self) -> List[Dict[str, Any]]:
        """Get all recorded security events"""
        pass
    
    @abstractmethod
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get complete audit trail of security-related changes"""
        pass
    
    @abstractmethod
    def clear_security_events(self) -> None:
        """Clear recorded security events"""
        pass
    
    @abstractmethod
    def clear_audit_trail(self) -> None:
        """Clear audit trail"""
        pass