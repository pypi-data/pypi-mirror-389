"""
EKS-optimized logger that outputs structured JSON to stdout
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from .interfaces import LogLevel

class EKSLogger:
    """EKS-optimized logger for structured JSON output to stdout"""
    
    def __init__(self, service_name: str = "graphrag-toolkit", namespace: str = "default"):
        self.service_name = service_name
        self.namespace = namespace
        self.pod_name = self._get_pod_name()
    
    def _get_pod_name(self) -> str:
        """Get pod name from environment or generate one"""
        import os
        return os.getenv('HOSTNAME', f"{self.service_name}-unknown")
    
    def _log_structured(self, level: str, message: str, **kwargs) -> None:
        """Output structured JSON log to stdout"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "service": self.service_name,
            "namespace": self.namespace,
            "pod": self.pod_name,
            **kwargs
        }
        
        # Output to stdout for EKS log collection
        print(json.dumps(log_entry), file=sys.stdout, flush=True)
    
    def info(self, msg: str, **kwargs) -> None:
        self._log_structured("INFO", msg, **kwargs)
    
    def debug(self, msg: str, **kwargs) -> None:
        self._log_structured("DEBUG", msg, **kwargs)
    
    def error(self, msg: str, **kwargs) -> None:
        self._log_structured("ERROR", msg, **kwargs)
    
    def critical(self, msg: str, **kwargs) -> None:
        self._log_structured("CRITICAL", msg, **kwargs)
    
    def warning(self, msg: str, **kwargs) -> None:
        self._log_structured("WARNING", msg, **kwargs)
    
    def warn(self, msg: str, **kwargs) -> None:
        """Alias for warning method"""
        self.warning(msg, **kwargs)
    
    def log_task_start(self, task_name: str, task_type: str = "System", **kwargs) -> None:
        self._log_structured("INFO", f"Task started: {task_name}", 
                           task_name=task_name, task_type=task_type, 
                           event_type="task_start", **kwargs)
    
    def log_task_stop(self, task_name: str, **kwargs) -> None:
        self._log_structured("INFO", f"Task completed: {task_name}", 
                           task_name=task_name, event_type="task_stop", **kwargs)
    
    def log_risk(self, msg: str, critical=False, minor=False, **kwargs) -> None:
        severity = "critical" if critical else "minor" if minor else "medium"
        self._log_structured("WARNING", f"Risk detected: {msg}", 
                           event_type="risk", risk_severity=severity, **kwargs)
    
    def log_anomaly(self, msg: str, **kwargs) -> None:
        self._log_structured("WARNING", f"Anomaly detected: {msg}", 
                           event_type="anomaly", **kwargs)