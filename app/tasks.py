import time
import logging
import random
from datetime import datetime
from sqlalchemy.orm import Session
from celery import current_task

from app.worker import celery
from app.database.database import SessionLocal
from app.models.task import Task, TaskStatus
from app.services.task import update_task, get_task
from app.schemas.task import InternalTaskUpdate

logger = logging.getLogger(__name__)


def get_db_session():
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


def set_task_status(db: Session, task_id: int, status: TaskStatus, result=None, error_info=None):
    task_update = InternalTaskUpdate(status=status)
    
    if result:
        task_update.result = result
    
    if error_info:
        task_update.error_info = error_info
        
    return update_task(db=db, task_id=task_id, task=task_update)


@celery.task(bind=True, name="process_task")
def process_task(self, task_id: int):
    celery_task_id = self.request.id
    logger.info(f"Processing task {task_id} (Celery task ID: {celery_task_id})")
    
    db = get_db_session()
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": f"Task {task_id} not found"}

        set_task_status(db, task_id, TaskStatus.PENDING)

        set_task_status(db, task_id, TaskStatus.IN_PROGRESS)

        if db_task.priority == "HIGH":
            processing_time = 5
        elif db_task.priority == "MEDIUM":
            processing_time = 10
        else:
            processing_time = 15

        for i in range(processing_time):
            if current_task.request.id != celery_task_id:
                logger.info(f"Task {task_id} was superseded by another task")
                return
                
            time.sleep(1)
            self.update_state(
                state="PROGRESS",
                meta={"current": i, "total": processing_time}
            )

        result = f"Task {task_id} completed successfully at {datetime.now().isoformat()}"
        set_task_status(db, task_id, TaskStatus.COMPLETED, result=result)
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        error_message = f"Error processing task {task_id}: {str(e)}"
        logger.error(error_message)
        set_task_status(db, task_id, TaskStatus.FAILED, error_info=error_message)
        return {"status": "error", "message": error_message}
    finally:
        db.close()


@celery.task(bind=True, name="process_broken_task")
def process_broken_task(self, task_id: int):
    celery_task_id = self.request.id
    logger.info(f"Processing broken task {task_id} (Celery task ID: {celery_task_id})")
    
    db = get_db_session()
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": f"Task {task_id} not found"}

        set_task_status(db, task_id, TaskStatus.PENDING)
        set_task_status(db, task_id, TaskStatus.IN_PROGRESS)

        time.sleep(2)

        raise ValueError("This task is deliberately broken and will always fail")
        
    except Exception as e:
        error_message = f"Error processing task {task_id}: {str(e)}"
        logger.error(error_message)
        set_task_status(db, task_id, TaskStatus.FAILED, error_info=error_message)
        return {"status": "error", "message": error_message}
    finally:
        db.close()


@celery.task(bind=True, max_retries=5, name="process_retry_task")
def process_retry_task(self, task_id: int, retry_count: int = 3):
    celery_task_id = self.request.id
    logger.info(f"Processing retry task {task_id} (Celery task ID: {celery_task_id})")
    
    db = get_db_session()
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": f"Task {task_id} not found"}

        set_task_status(db, task_id, TaskStatus.PENDING)
        set_task_status(db, task_id, TaskStatus.IN_PROGRESS)

        time.sleep(2)

        if self.request.retries < retry_count and random.random() < 0.7:
            error_msg = f"Random failure (attempt {self.request.retries + 1}/{retry_count})"
            set_task_status(db, task_id, TaskStatus.PENDING, error_info=error_msg)
            logger.info(f"Task {task_id} failed with: {error_msg}. Retrying...")
            raise self.retry(countdown=3, exc=Exception(error_msg))

        result = f"Task {task_id} completed successfully after {self.request.retries} retries at {datetime.now().isoformat()}"
        set_task_status(db, task_id, TaskStatus.COMPLETED, result=result)
        
        return {"status": "success", "result": result}
        
    except self.MaxRetriesExceededError:
        error_message = f"Task {task_id} failed after maximum retries ({retry_count})"
        logger.error(error_message)
        set_task_status(db, task_id, TaskStatus.FAILED, error_info=error_message)
        return {"status": "error", "message": error_message}
    except Exception as e:
        if self.request.retries >= retry_count:
            error_message = f"Task {task_id} failed after maximum retries: {str(e)}"
            logger.error(error_message)
            set_task_status(db, task_id, TaskStatus.FAILED, error_info=error_message)
            return {"status": "error", "message": error_message}
        raise
    finally:
        db.close()


@celery.task(name="cancel_task")
def cancel_task(task_id: int):
    db = get_db_session()
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            return {"status": "error", "message": f"Task {task_id} not found"}
            
        if db_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return {"status": "error", "message": f"Task {task_id} is already in final state: {db_task.status}"}
            
        set_task_status(db, task_id, TaskStatus.CANCELLED, result="Task was cancelled")
        return {"status": "success", "message": f"Task {task_id} cancelled"}
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
