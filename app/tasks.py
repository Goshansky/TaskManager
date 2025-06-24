import logging
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.worker import register_task_handler
from app.database.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.schemas.task import InternalTaskUpdate

logger = logging.getLogger(__name__)


async def get_db_session():
    db = AsyncSessionLocal()
    try:
        return db
    except Exception as e:
        await db.close()
        raise e


async def get_task(db: AsyncSession, task_id: int):
    result = await db.execute(select(Task).filter(Task.id == task_id))
    return result.scalars().first()


async def set_task_status(
    db: AsyncSession, task_id: int, status: TaskStatus, result=None, error_info=None
):
    task_update = InternalTaskUpdate(status=status)

    if result:
        task_update.result = result

    if error_info:
        task_update.error_info = error_info

    task = await get_task(db, task_id)
    if not task:
        return None

    update_data = task_update.dict(exclude_unset=True)

    if "status" in update_data:
        new_status = update_data["status"]

        if (
            new_status == TaskStatus.IN_PROGRESS
            and task.status != TaskStatus.IN_PROGRESS
        ):
            task.started_at = datetime.now()

        if (
            new_status
            in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            and task.completed_at is None
        ):
            task.completed_at = datetime.now()

    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@register_task_handler("process_task")
async def process_task(task_id: int):
    logger.info(f"Processing task {task_id}")

    db = await get_db_session()
    try:
        task = await get_task(db, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": f"Task {task_id} not found"}

        if task.status == TaskStatus.CANCELLED:
            logger.info(f"Task {task_id} was cancelled before processing")
            return {"status": "cancelled", "message": f"Task {task_id} was cancelled"}

        await set_task_status(db, task_id, TaskStatus.PENDING)

        task = await get_task(db, task_id)
        if task.status == TaskStatus.CANCELLED:
            logger.info(f"Task {task_id} was cancelled while setting status to PENDING")
            return {"status": "cancelled", "message": f"Task {task_id} was cancelled"}

        await set_task_status(db, task_id, TaskStatus.IN_PROGRESS)

        task = await get_task(db, task_id)
        if task.status == TaskStatus.CANCELLED:
            logger.info(
                f"Task {task_id} was cancelled while setting status to IN_PROGRESS"
            )
            return {"status": "cancelled", "message": f"Task {task_id} was cancelled"}

        if task.priority == "HIGH":
            processing_time = 5
        elif task.priority == "MEDIUM":
            processing_time = 10
        else:
            processing_time = 15

        for i in range(processing_time):
            task = await get_task(db, task_id)
            if task.status == TaskStatus.CANCELLED:
                logger.info(f"Task {task_id} was cancelled during processing")
                return {
                    "status": "cancelled",
                    "message": f"Task {task_id} was cancelled",
                }

            await asyncio.sleep(1)
            logger.info(f"Task {task_id} progress: {i+1}/{processing_time}")

        task = await get_task(db, task_id)
        if task.status == TaskStatus.CANCELLED:
            logger.info(f"Task {task_id} was cancelled before completion")
            return {"status": "cancelled", "message": f"Task {task_id} was cancelled"}

        result = (
            f"Task {task_id} completed successfully at {datetime.now().isoformat()}"
        )
        await set_task_status(db, task_id, TaskStatus.COMPLETED, result=result)

        return {"status": "success", "result": result}

    except Exception as e:
        error_message = f"Error processing task {task_id}: {str(e)}"
        logger.error(error_message)
        await set_task_status(db, task_id, TaskStatus.FAILED, error_info=error_message)
        return {"status": "error", "message": error_message}
    finally:
        await db.close()


@register_task_handler("process_broken_task")
async def process_broken_task(task_id: int):
    logger.info(f"Processing broken task {task_id}")

    db = await get_db_session()
    try:
        task = await get_task(db, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": f"Task {task_id} not found"}

        if task.status == TaskStatus.CANCELLED:
            logger.info(f"Task {task_id} was cancelled before processing")
            return {"status": "cancelled", "message": f"Task {task_id} was cancelled"}

        await set_task_status(db, task_id, TaskStatus.PENDING)

        task = await get_task(db, task_id)
        if task.status == TaskStatus.CANCELLED:
            logger.info(f"Task {task_id} was cancelled while setting status to PENDING")
            return {"status": "cancelled", "message": f"Task {task_id} was cancelled"}

        await set_task_status(db, task_id, TaskStatus.IN_PROGRESS)

        await asyncio.sleep(2)

        result = "This task was deliberately broken"
        await set_task_status(
            db,
            task_id,
            TaskStatus.FAILED,
            result=result,
            error_info="This task is deliberately broken and will always fail",
        )

        return {
            "status": "error",
            "message": "This task is deliberately broken and will always fail",
        }

    except Exception as e:
        error_message = f"Error processing task {task_id}: {str(e)}"
        logger.error(error_message)
        await set_task_status(db, task_id, TaskStatus.FAILED, error_info=error_message)
        return {"status": "error", "message": error_message}
    finally:
        await db.close()
