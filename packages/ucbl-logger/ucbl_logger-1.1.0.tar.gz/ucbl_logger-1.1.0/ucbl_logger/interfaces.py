from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ILogger(ABC):
    """Basic logging interface with enhanced capabilities support"""
    @abstractmethod
    def log(self, level: LogLevel, message: str) -> None:
        pass
    
    # Enhanced logging methods with optional correlation ID support
    def info(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log info message with optional correlation ID and context"""
        self.log(LogLevel.INFO, msg)
    
    def debug(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log debug message with optional correlation ID and context"""
        self.log(LogLevel.DEBUG, msg)
    
    def error(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log error message with optional correlation ID and context"""
        self.log(LogLevel.ERROR, msg)
    
    def critical(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log critical message with optional correlation ID and context"""
        self.log(LogLevel.CRITICAL, msg)
    
    def warning(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log warning message with optional correlation ID and context"""
        self.log(LogLevel.WARNING, msg)

class ITaskLogger(ABC):
    """Task-specific logging interface with enhanced tracing support"""
    @abstractmethod
    def log_task_start(self, task_name: str, task_type: str = "System") -> None:
        pass
    
    @abstractmethod
    def log_task_stop(self, task_name: str) -> None:
        pass
    
    # Enhanced task logging with correlation ID support
    def log_task_start_enhanced(self, task_name: str, task_type: str = "System", 
                              correlation_id: Optional[str] = None, **kwargs) -> Optional[str]:
        """Start task with enhanced tracing - returns correlation ID if tracing enabled"""
        self.log_task_start(task_name, task_type)
        return correlation_id
    
    def log_task_stop_enhanced(self, task_name: str, correlation_id: Optional[str] = None, 
                             success: bool = True, **kwargs) -> None:
        """Stop task with enhanced tracing"""
        self.log_task_stop(task_name)

class IRiskLogger(ABC):
    """Risk and anomaly logging interface with enhanced context"""
    @abstractmethod
    def log_risk(self, message: str, critical: bool = False, minor: bool = False) -> None:
        pass
    
    @abstractmethod
    def log_anomaly(self, message: str) -> None:
        pass
    
    # Enhanced risk logging with correlation ID and security context
    def log_risk_enhanced(self, message: str, critical: bool = False, minor: bool = False,
                         correlation_id: Optional[str] = None, security_context: Optional[Dict[str, Any]] = None,
                         **kwargs) -> None:
        """Log risk with enhanced security and tracing context"""
        self.log_risk(message, critical, minor)
    
    def log_anomaly_enhanced(self, message: str, correlation_id: Optional[str] = None,
                           performance_context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log anomaly with enhanced performance and tracing context"""
        self.log_anomaly(message)

class ITimeProvider(ABC):
    """Time provider interface"""
    @abstractmethod
    def get_current_time(self) -> str:
        pass
    
    @abstractmethod
    def set_timezone(self, timezone: str) -> None:
        pass

class IMessageFormatter(ABC):
    """Message formatting interface"""
    @abstractmethod
    def format_message(self, message: str, context: Dict[str, Any]) -> str:
        pass

class ITaskTypeProvider(ABC):
    """Task type provider interface"""
    @abstractmethod
    def get_task_types(self) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def is_valid_task_type(self, task_type: str) -> bool:
        pass

class IMarkupProvider(ABC):
    """Markup provider interface"""
    @abstractmethod
    def mark_goal(self, goal: str) -> str:
        pass
    
    @abstractmethod
    def mark_operator(self, operator: str) -> str:
        pass
    
    @abstractmethod
    def mark_method(self, method: str) -> str:
        pass