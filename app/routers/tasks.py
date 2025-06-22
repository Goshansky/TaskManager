from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, BrokenTaskCreate
from app.services import create_task, get_task, get_tasks, update_task, delete_task, cancel_task, create_broken_task

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    return await create_task(db=db, task=task)


@router.post("/broken", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_broken_task(task: BrokenTaskCreate, db: AsyncSession = Depends(get_db)):
    return await create_broken_task(db=db, task=task)


@router.get("/", response_model=List[TaskResponse])
async def read_tasks(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    return await get_tasks(db=db, skip=skip, limit=limit, status=status, priority=priority)


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(task_id: int, db: AsyncSession = Depends(get_db)):
    db_task = await get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_existing_task(task_id: int, task: TaskUpdate, db: AsyncSession = Depends(get_db)):
    db_task = await get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    restricted_update = TaskUpdate(
        title=task.title,
        description=task.description,
        priority=task.priority
    )
    
    return await update_task(db=db, task_id=task_id, task=restricted_update)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(task_id: int, db: AsyncSession = Depends(get_db)):
    db_task = await get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await delete_task(db=db, task_id=task_id)
    return None


@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_existing_task(task_id: int, db: AsyncSession = Depends(get_db)):
    db_task = await get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = await cancel_task(db=db, task_id=task_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
