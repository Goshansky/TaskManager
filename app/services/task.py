from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


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
    return db_task


def update_task(db: Session, task_id: int, task: TaskUpdate):
    db_task = get_task(db, task_id)
    
    update_data = task.dict(exclude_unset=True)

    if "status" in update_data:
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
