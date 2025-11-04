from typing import Optional, Dict, Any
from .interfaces import IRiskLogger, ILogger, IMessageFormatter, LogLevel

class RiskLogger(IRiskLogger):
    """Risk and anomaly logging implementation - Single Responsibility"""
    
    def __init__(self, 
                 core_logger: ILogger,
                 formatter: IMessageFormatter):
        self._core_logger = core_logger
        self._formatter = formatter
    
    def log_risk(self, message: str, critical: bool = False, minor: bool = False) -> None:
        """Log a risk with appropriate severity"""
        context = {"task_type": "System"}
        formatted_message = self._formatter.format_message(message, context)
        
        if critical:
            risk_message = f"~CRITICAL RISK~ {formatted_message} ~CRITICAL RISK~"
            self._core_logger.log(LogLevel.CRITICAL, risk_message)
        elif minor:
            risk_message = f"~MINOR RISK~ {formatted_message} ~MINOR RISK~"
            self._core_logger.log(LogLevel.INFO, risk_message)
        else:
            risk_message = f"~RISK~ {formatted_message} ~RISK~"
            self._core_logger.log(LogLevel.WARNING, risk_message)
    
    def log_anomaly(self, message: str) -> None:
        """Log an anomaly detection"""
        context = {"task_type": "System"}
        anomaly_message = f"Anomaly Detected: {message}"
        formatted_message = self._formatter.format_message(anomaly_message, context)
        
        final_message = f"~ANOMALY~ {formatted_message} ~ANOMALY~"
        self._core_logger.log(LogLevel.WARNING, final_message)
    
    def log_suspicious_activity(self, message: str) -> None:
        """Log suspicious activity"""
        context = {"task_type": "System"}
        suspicious_message = f"Suspicious Activity: {message}"
        formatted_message = self._formatter.format_message(suspicious_message, context)
        
        final_message = f"~SUSPICIOUS~ {formatted_message} ~SUSPICIOUS~"
        self._core_logger.log(LogLevel.WARNING, final_message)