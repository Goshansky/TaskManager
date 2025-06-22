from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routers import tasks_router
from app.worker import get_connection, shutdown_worker
from app.monitoring import setup_monitoring

app = FastAPI(
    title="Task Manager API",
    description="Asynchronous Task Manager API with task queue and priority processing",
    version="1.0.0"
)

app.include_router(tasks_router)


@app.on_event("startup")
async def startup_db_client():
    await get_connection()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown_db_client():
    await shutdown_worker()


@app.get("/")
async def root():
    return {"message": "Task Manager API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

setup_monitoring(app)
