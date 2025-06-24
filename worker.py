import asyncio
import logging
from app.worker import start_worker
import app.tasks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting task worker...")
    asyncio.run(start_worker())
