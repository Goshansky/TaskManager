from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, BrokenTaskCreate, InternalTaskUpdate


async def get_task(db: AsyncSession, task_id: int):
    result = await db.execute(select(Task).filter(Task.id == task_id))
    return result.scalars().first()


async def get_tasks(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    query = select(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_task(db: AsyncSession, task: TaskCreate):
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.NEW
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    from app.worker import publish_task

    priority_value = 10 if db_task.priority == TaskPriority.HIGH else (
        5 if db_task.priority == TaskPriority.MEDIUM else 1
    )

    await publish_task(
        task_type="process_task",
        payload={"task_id": db_task.id},
        priority=priority_value
    )
    
    return db_task


async def create_broken_task(db: AsyncSession, task: BrokenTaskCreate):
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.NEW
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    from app.worker import publish_task

    await publish_task(
        task_type="process_broken_task",
        payload={"task_id": db_task.id}
    )
    
    return db_task


async def update_task(db: AsyncSession, task_id: int, task: Union[TaskUpdate, InternalTaskUpdate]):
    db_task = await get_task(db, task_id)
    
    update_data = task.dict(exclude_unset=True)

    if isinstance(task, InternalTaskUpdate) and "status" in update_data:
        new_status = update_data["status"]

        if new_status == TaskStatus.IN_PROGRESS and db_task.status != TaskStatus.IN_PROGRESS:
            update_data["started_at"] = datetime.now()

        if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and db_task.completed_at is None:
            update_data["completed_at"] = datetime.now()
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def delete_task(db: AsyncSession, task_id: int):
    db_task = await get_task(db, task_id)
    await db.delete(db_task)
    await db.commit()
    return db_task


async def cancel_task(db: AsyncSession, task_id: int) -> Dict[str, Any]:
    db_task = await get_task(db, task_id)
    
    if not db_task:
        return {"success": False, "message": "Task not found"}
    
    if db_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        return {"success": False, "message": f"Task is already in final state: {db_task.status}"}

    task_update = InternalTaskUpdate(
        status=TaskStatus.CANCELLED,
        result=f"Task was cancelled at {datetime.now().isoformat()}"
    )

    await update_task(db=db, task_id=task_id, task=task_update)
    
    return {"success": True, "message": "Task cancelled successfully"}
