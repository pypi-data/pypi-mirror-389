import time
from typing import List, Tuple, Optional
from .interfaces import ITaskLogger, ILogger, IMessageFormatter, ITimeProvider, ITaskTypeProvider, LogLevel

class TaskLogger(ITaskLogger):
    """Task logging implementation - Single Responsibility for task management"""
    
    def __init__(self, 
                 core_logger: ILogger,
                 formatter: IMessageFormatter,
                 time_provider: ITimeProvider,
                 task_type_provider: ITaskTypeProvider):
        self._core_logger = core_logger
        self._formatter = formatter
        self._time_provider = time_provider
        self._task_type_provider = task_type_provider
        self._task_stack: List[Tuple[str, float]] = []
        self._current_task_type = "System"
        self._slow_threshold = 5.0
    
    def log_task_start(self, task_name: str, task_type: str = "System") -> None:
        """Log the start of a task"""
        if not self._task_type_provider.is_valid_task_type(task_type):
            task_type = "System"
        
        self._current_task_type = task_type
        start_time = time.time()
        self._task_stack.append((task_name, start_time))
        
        context = {"task_type": task_type}
        timestamp = self._time_provider.get_current_time()
        message = f"Task '<# {task_name} #>' started at {timestamp}."
        formatted_message = self._formatter.format_message(message, context)
        
        self._core_logger.log(LogLevel.INFO, formatted_message)
    
    def log_task_stop(self, task_name: str) -> None:
        """Log the stop of a task and calculate duration"""
        if not self._task_stack:
            self._core_logger.log(LogLevel.WARNING, f"Task '<# {task_name} #>' stop called without start.")
            return
        
        _, start_time = self._task_stack.pop()
        duration = time.time() - start_time
        
        context = {"task_type": self._current_task_type}
        timestamp = self._time_provider.get_current_time()
        message = f"Task '<# {task_name} #>' stopped at {timestamp}. Duration: {duration:.2f} seconds."
        formatted_message = self._formatter.format_message(message, context)
        
        if duration > self._slow_threshold:
            slow_message = f"~SLOW_TASK~ Task '<# {task_name} #>' took longer than expected."
            self._core_logger.log(LogLevel.WARNING, slow_message)
        
        self._core_logger.log(LogLevel.INFO, formatted_message)
    
    def set_slow_threshold(self, threshold: float) -> None:
        """Set the threshold for slow task detection"""
        self._slow_threshold = max(0.0, threshold)