from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, BrokenTaskCreate, RetryTaskCreate
from app.services import create_task, get_task, get_tasks, update_task, delete_task, cancel_task, create_broken_task, create_retry_task

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(task: TaskCreate, db: Session = Depends(get_db)):
    return create_task(db=db, task=task)


@router.post("/broken", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_broken_task(task: BrokenTaskCreate, db: Session = Depends(get_db)):
    return create_broken_task(db=db, task=task)


@router.post("/retry", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_retry_task(task: RetryTaskCreate, db: Session = Depends(get_db)):
    return create_retry_task(db=db, task=task)


@router.get("/", response_model=List[TaskResponse])
def read_tasks(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return get_tasks(db=db, skip=skip, limit=limit, status=status, priority=priority)


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/{task_id}", response_model=TaskResponse)
def update_existing_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    restricted_update = TaskUpdate(
        title=task.title,
        description=task.description,
        priority=task.priority
    )
    
    return update_task(db=db, task_id=task_id, task=restricted_update)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_task(task_id: int, db: Session = Depends(get_db)):
    db_task = get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    delete_task(db=db, task_id=task_id)
    return None


@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
def cancel_existing_task(task_id: int, db: Session = Depends(get_db)):
    db_task = get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = cancel_task(db=db, task_id=task_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
