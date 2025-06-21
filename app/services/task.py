from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, BrokenTaskCreate, RetryTaskCreate, InternalTaskUpdate


def get_task(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    return query.offset(skip).limit(limit).all()


def create_task(db: Session, task: TaskCreate):
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.NEW
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    from app.tasks import process_task

    priority_value = 3 if db_task.priority == TaskPriority.HIGH else (
        2 if db_task.priority == TaskPriority.MEDIUM else 1
    )

    process_task.apply_async(
        args=[db_task.id],
        priority=priority_value
    )
    
    return db_task


def create_broken_task(db: Session, task: BrokenTaskCreate):
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.NEW
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    from app.tasks import process_broken_task

    process_broken_task.apply_async(
        args=[db_task.id],
    )
    
    return db_task


def create_retry_task(db: Session, task: RetryTaskCreate):
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.NEW
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    from app.tasks import process_retry_task

    process_retry_task.apply_async(
        args=[db_task.id, task.retry_count],
    )
    
    return db_task


def update_task(db: Session, task_id: int, task: Union[TaskUpdate, InternalTaskUpdate]):
    db_task = get_task(db, task_id)
    
    update_data = task.dict(exclude_unset=True)

    # Handle status changes (only for InternalTaskUpdate)
    if isinstance(task, InternalTaskUpdate) and "status" in update_data:
        new_status = update_data["status"]

        if new_status == TaskStatus.IN_PROGRESS and db_task.status != TaskStatus.IN_PROGRESS:
            update_data["started_at"] = datetime.now()

        if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and db_task.completed_at is None:
            update_data["completed_at"] = datetime.now()
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    db.delete(db_task)
    db.commit()
    return db_task


def cancel_task(db: Session, task_id: int) -> Dict[str, Any]:
    db_task = get_task(db, task_id)
    
    if not db_task:
        return {"success": False, "message": "Task not found"}
    
    if db_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        return {"success": False, "message": f"Task is already in final state: {db_task.status}"}

    from app.tasks import cancel_task as celery_cancel_task

    celery_cancel_task.delay(task_id)
    
    return {"success": True, "message": "Task cancellation initiated"}
