import asyncio
import logging
import os
from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy import func, text
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.worker import get_connection, get_channel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitor",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)


async def get_rabbitmq_stats():
    try:
        connection = await get_connection()
        channel = await get_channel()

        queue = await channel.get_queue("task_queue")

        message_count = queue.declaration_result.message_count
        consumer_count = queue.declaration_result.consumer_count
        
        return {
            "queue_name": "task_queue",
            "message_count": message_count,
            "consumer_count": consumer_count,
            "connection_status": "connected" if not connection.is_closed else "disconnected",
        }
    except Exception as e:
        logger.error(f"Error getting RabbitMQ stats: {str(e)}")
        return {
            "queue_name": "task_queue",
            "message_count": "error",
            "consumer_count": "error",
            "connection_status": "error",
            "error": str(e)
        }


async def get_task_stats(db: AsyncSession, page: int = 1, page_size: int = 10):
    try:
        status_counts = {}
        for status in TaskStatus:
            query = select(func.count()).select_from(Task).filter(Task.status == status)
            result = await db.execute(query)
            count = result.scalar()
            status_counts[status.value] = count

        priority_counts = {}
        for priority in TaskPriority:
            query = select(func.count()).select_from(Task).filter(Task.priority == priority)
            result = await db.execute(query)
            count = result.scalar()
            priority_counts[priority.value] = count

        query = select(func.count()).select_from(Task)
        result = await db.execute(query)
        total_count = result.scalar()

        offset = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        query = select(Task).order_by(Task.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        tasks = result.scalars().all()

        query = text("""
            SELECT 
                AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_time,
                MIN(EXTRACT(EPOCH FROM (completed_at - started_at))) as min_time,
                MAX(EXTRACT(EPOCH FROM (completed_at - started_at))) as max_time
            FROM tasks 
            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
        """)
        result = await db.execute(query)
        time_stats = result.first()
        
        return {
            "total_tasks": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result,
                    "error_info": task.error_info
                }
                for task in tasks
            ],
            "processing_time": {
                "avg_seconds": round(time_stats[0] or 0, 2) if time_stats else 0,
                "min_seconds": round(time_stats[1] or 0, 2) if time_stats else 0,
                "max_seconds": round(time_stats[2] or 0, 2) if time_stats else 0,
            }
        }
    except Exception as e:
        logger.error(f"Error getting task stats: {str(e)}")
        return {
            "error": str(e)
        }


@router.get("/stats", response_model=Dict[str, Any])
async def get_monitor_stats(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    rabbitmq_stats = await get_rabbitmq_stats()
    task_stats = await get_task_stats(db, page, page_size)
    
    return {
        "rabbitmq": rabbitmq_stats,
        "tasks": task_stats,
        "timestamp": asyncio.get_event_loop().time()
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def get_monitor_dashboard():
    try:
        dashboard_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")

        logger.info(f"Loading dashboard template from: {dashboard_path}")

        if os.path.exists(dashboard_path):
            try:
                with open(dashboard_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.warning(f"Failed to read {dashboard_path} with UTF-8 encoding, trying with latin-1")
                with open(dashboard_path, "r", encoding="latin-1") as f:
                    return f.read()
        else:
            error_message = f"Dashboard template file not found at {dashboard_path}"
            logger.error(error_message)
            return f"<h1>Error: Dashboard template not found</h1><p>Path: {dashboard_path}</p>"
    except Exception as e:
        logger.error(f"Error loading dashboard template: {str(e)}")
        return f"<h1>Error loading dashboard</h1><p>{str(e)}</p>"


def setup_monitoring(app: FastAPI):
    """Add monitoring routes to the FastAPI app"""
    app.include_router(router)
