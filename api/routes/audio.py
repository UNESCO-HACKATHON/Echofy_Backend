from typing import Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from tasks.processor import process_audio_task

router = APIRouter()

@router.post("/analyze/audio/")
async def analyze_audio(audio_file: UploadFile = File(...), background_tasks: Optional[BackgroundTasks] = None):
    try:
        task_id = await process_audio_task(audio_file, background_tasks)
        return {"message": "Audio received. Process started.", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")