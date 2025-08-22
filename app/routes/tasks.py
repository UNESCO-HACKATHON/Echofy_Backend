from fastapi import APIRouter, HTTPException
from app.tasks.processors import tasks

router = APIRouter()

@router.get("/tasks")
async def list_tasks():
    return tasks

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    if task_id in tasks:
        return tasks[task_id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")