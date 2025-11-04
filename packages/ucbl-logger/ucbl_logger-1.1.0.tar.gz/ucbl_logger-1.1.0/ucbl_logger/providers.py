import datetime
import pytz
import logging
import inspect
from typing import Dict, Any
from .interfaces import ITimeProvider, IMessageFormatter, ITaskTypeProvider, IMarkupProvider

class TimeProvider(ITimeProvider):
    """Concrete time provider implementation"""
    
    def __init__(self, timezone_str: str = 'UTC'):
        self._timezone = pytz.timezone(timezone_str)
    
    def get_current_time(self) -> str:
        now = datetime.datetime.now(self._timezone)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    def set_timezone(self, timezone: str) -> None:
        try:
            self._timezone = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            self._timezone = pytz.utc

class MessageFormatter(IMessageFormatter):
    """Concrete message formatter implementation"""
    
    def __init__(self, task_type_provider: ITaskTypeProvider, stack_level: int = 3):
        self._task_type_provider = task_type_provider
        self._stack_level = stack_level
    
    def format_message(self, message: str, context: Dict[str, Any]) -> str:
        location_info = self._get_location_info()
        task_type = context.get('task_type', 'System')
        task_type_info = f"[{self._task_type_provider.get_task_types().get(task_type, 'UNKNOWN_TASK')}]"
        return f'{location_info} - {task_type_info} - {message}'.strip()
    
    def _get_location_info(self) -> str:
        try:
            caller = inspect.stack()[self._stack_level]
            filename = caller.filename.split('/')[-1]
            line_number = caller.lineno
            function_name = caller.function
            return f'[File: {filename}] [Function: {function_name}] [Line: {line_number}]'
        except IndexError:
            return '[File: unknown] [Function: unknown] [Line: unknown]'

class DefaultTaskTypeProvider(ITaskTypeProvider):
    """Default task type provider implementation"""
    
    def __init__(self):
        self._task_types = {
            "User": "USER_TASK",
            "System": "SYSTEM_TASK",
            "SystemUser": "SYSTEM_USER_TASK",
            "AdminUser": "ADMIN_USER_TASK",
            "EndUser": "END_USER_TASK",
            "ExternalUser": "EXTERNAL_USER_TASK",
            "SystemInternal": "SYSTEM_INTERNAL_TASK",
            "SystemSecurity": "SYSTEM_SECURITY_TASK",
            "SystemMaintenance": "SYSTEM_MAINTENANCE_TASK",
            "UserInitiatedSystemTask": "USER_INITIATED_SYSTEM_TASK",
            "SystemInitiatedUserTask": "SYSTEM_INITIATED_USER_TASK"
        }
    
    def get_task_types(self) -> Dict[str, str]:
        return self._task_types.copy()
    
    def is_valid_task_type(self, task_type: str) -> bool:
        return task_type in self._task_types

class DefaultMarkupProvider(IMarkupProvider):
    """Default markup provider implementation"""
    
    def mark_goal(self, goal: str) -> str:
        return f'<Goal: {goal}>'
    
    def mark_operator(self, operator: str) -> str:
        return f'<Op: {operator}>'
    
    def mark_method(self, method: str) -> str:
        return f'<Method: {method}>'