from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routers import tasks_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Manager API",
    description="Asynchronous Task Manager API with task queue and priority processing",
    version="1.0.0"
)

app.include_router(tasks_router)


@app.get("/")
async def root():
    return {"message": "Task Manager API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
