from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Request
from api.tasks.processors import process_image_task

router = APIRouter()

@router.post("/analyze/image/")
async def analyze_image(image_file: UploadFile, background_tasks: BackgroundTasks, request : Request):
    try:
        task_id = await process_image_task(image_file, background_tasks)
        base_url = str(request.base_url).rstrip("/")
        return {
            "message": "Audio received. Process started.",
            "task_id": task_id,
            "status_path": f"{base_url}/api/tasks/{task_id}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))