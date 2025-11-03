"""
数据库模型定义

所有表的 SQLAlchemy 模型定义
"""

from .task import Task
from .task_run import TaskRun
from .scheduled_task import ScheduledTask, TaskExecutionHistory

# 为了向后兼容，从 core.enums 导出枚举
from jettask.core.enums import TaskType, TaskStatus

__all__ = [
    'Task',
    'TaskRun',
    'ScheduledTask',
    'TaskExecutionHistory',
    'TaskType',
    'TaskStatus',
]
