from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskCreate(TaskBase):
    pass


class BrokenTaskCreate(TaskBase):
    force_error: bool = True


class RetryTaskCreate(TaskBase):
    retry_count: int = Field(default=3, ge=1, le=5)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None


class InternalTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    result: Optional[str] = None
    error_info: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error_info: Optional[str] = None

    class Config:
        from_attributes = True
