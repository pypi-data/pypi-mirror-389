from .interfaces import ILogger, ITaskLogger, IRiskLogger, LogLevel
from .core_logger import CoreLogger
from .task_logger import TaskLogger
from .risk_logger import RiskLogger
from .providers import TimeProvider, MessageFormatter, DefaultTaskTypeProvider, DefaultMarkupProvider

class UCBLLoggerFactory:
    """Factory for creating SOLID-compliant logger instances"""
    
    @staticmethod
    def create_basic_logger(logger_name: str = __name__, 
                          log_level: LogLevel = LogLevel.INFO) -> ILogger:
        """Create a basic logger instance"""
        return CoreLogger(logger_name, log_level)
    
    @staticmethod
    def create_task_logger(logger_name: str = __name__, 
                          log_level: LogLevel = LogLevel.INFO,
                          timezone: str = 'UTC') -> ITaskLogger:
        """Create a task logger instance"""
        core_logger = CoreLogger(logger_name, log_level)
        time_provider = TimeProvider(timezone)
        task_type_provider = DefaultTaskTypeProvider()
        formatter = MessageFormatter(task_type_provider)
        
        return TaskLogger(core_logger, formatter, time_provider, task_type_provider)
    
    @staticmethod
    def create_risk_logger(logger_name: str = __name__, 
                          log_level: LogLevel = LogLevel.INFO) -> IRiskLogger:
        """Create a risk logger instance"""
        core_logger = CoreLogger(logger_name, log_level)
        task_type_provider = DefaultTaskTypeProvider()
        formatter = MessageFormatter(task_type_provider)
        
        return RiskLogger(core_logger, formatter)
    
    @staticmethod
    def create_complete_logger(logger_name: str = __name__, 
                             log_level: LogLevel = LogLevel.INFO,
                             timezone: str = 'UTC') -> 'CompleteLogger':
        """Create a complete logger with all capabilities"""
        core_logger = CoreLogger(logger_name, log_level)
        time_provider = TimeProvider(timezone)
        task_type_provider = DefaultTaskTypeProvider()
        formatter = MessageFormatter(task_type_provider)
        
        task_logger = TaskLogger(core_logger, formatter, time_provider, task_type_provider)
        risk_logger = RiskLogger(core_logger, formatter)
        
        return CompleteLogger(core_logger, task_logger, risk_logger)

class CompleteLogger:
    """Composite logger that combines all logging capabilities"""
    
    def __init__(self, 
                 core_logger: ILogger,
                 task_logger: ITaskLogger,
                 risk_logger: IRiskLogger):
        self._core = core_logger
        self._task = task_logger
        self._risk = risk_logger
    
    # Basic logging methods
    def info(self, message: str) -> None:
        self._core.log(LogLevel.INFO, message)
    
    def debug(self, message: str) -> None:
        self._core.log(LogLevel.DEBUG, message)
    
    def warning(self, message: str) -> None:
        self._core.log(LogLevel.WARNING, message)
    
    def warn(self, message: str) -> None:
        """Alias for warning method"""
        self.warning(message)
    
    def error(self, message: str) -> None:
        self._core.log(LogLevel.ERROR, message)
    
    def critical(self, message: str) -> None:
        self._core.log(LogLevel.CRITICAL, message)
    
    # Task logging methods
    def log_task_start(self, task_name: str, task_type: str = "System") -> None:
        self._task.log_task_start(task_name, task_type)
    
    def log_task_stop(self, task_name: str) -> None:
        self._task.log_task_stop(task_name)
    
    # Risk logging methods
    def log_risk(self, message: str, critical: bool = False, minor: bool = False) -> None:
        self._risk.log_risk(message, critical, minor)
    
    def log_anomaly(self, message: str) -> None:
        self._risk.log_anomaly(message)