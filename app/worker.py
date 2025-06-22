import asyncio
import json
import logging
from typing import Dict, Any, Callable, Coroutine, Optional
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from app.config import RABBITMQ_URL, TASK_QUEUE_NAME, TASK_CONCURRENCY

logger = logging.getLogger(__name__)

_connection: Optional[aio_pika.Connection] = None
_channel: Optional[aio_pika.Channel] = None
_task_handlers: Dict[str, Callable] = {}


async def get_connection() -> aio_pika.Connection:
    global _connection
    
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(1, max_retries + 1):
        try:
            if _connection is None or _connection.is_closed:
                logger.info(f"Connecting to RabbitMQ (attempt {attempt}/{max_retries})...")
                _connection = await aio_pika.connect_robust(RABBITMQ_URL)
                logger.info("Successfully connected to RabbitMQ")
            return _connection
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Failed to connect to RabbitMQ (attempt {attempt}/{max_retries}): {str(e)}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {str(e)}")
                raise


async def get_channel() -> aio_pika.Channel:
    global _channel
    
    if _channel is None or _channel.is_closed:
        connection = await get_connection()
        _channel = await connection.channel()

        await _channel.declare_queue(
            TASK_QUEUE_NAME, 
            durable=True,
            arguments={"x-max-priority": 10}
        )
        
    return _channel


async def publish_task(task_type: str, payload: Dict[str, Any], priority: int = 0) -> None:
    channel = await get_channel()
    message_body = json.dumps({
        "task_type": task_type,
        "payload": payload
    }).encode()
    
    message = aio_pika.Message(
        body=message_body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        priority=priority
    )
    
    await channel.default_exchange.publish(
        message,
        routing_key=TASK_QUEUE_NAME
    )
    
    logger.info(f"Published task: {task_type} with payload: {payload}")


def register_task_handler(task_type: str):
    def decorator(func: Callable):
        _task_handlers[task_type] = func
        logger.info(f"Registered task handler for type: {task_type}")
        return func
    return decorator


async def process_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            message_data = json.loads(message.body.decode())
            task_type = message_data.get("task_type")
            payload = message_data.get("payload", {})
            
            logger.info(f"Processing task: {task_type} with payload: {payload}")

            if task_type in _task_handlers:
                handler = _task_handlers[task_type]
                await handler(**payload)
            else:
                logger.error(f"No handler registered for task type: {task_type}")
                logger.error(f"Registered handlers: {list(_task_handlers.keys())}")
                
        except Exception as e:
            logger.exception(f"Error processing message: {e}")


async def start_worker() -> None:
    try:
        from app.tasks import process_task, process_broken_task
        
        logger.info(f"Registered task handlers: {list(_task_handlers.keys())}")
        
        channel = await get_channel()
        queue = await channel.get_queue(TASK_QUEUE_NAME)

        await channel.set_qos(prefetch_count=TASK_CONCURRENCY)
        
        logger.info(f"Starting worker with concurrency: {TASK_CONCURRENCY}")

        await queue.consume(process_message)

        await asyncio.Future()
    except Exception as e:
        logger.exception(f"Error starting worker: {e}")
        await asyncio.sleep(5)
        return await start_worker()
    finally:
        if _connection and not _connection.is_closed:
            await _connection.close()


async def shutdown_worker() -> None:
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("Worker connection closed")
