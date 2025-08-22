from fastapi import APIRouter, HTTPException

from tasks.processor import tasks

router = APIRouter()

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    if task_id in tasks:
        return tasks[task_id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")