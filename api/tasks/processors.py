import os
import tempfile
import asyncio

from fastapi import BackgroundTasks, UploadFile

from ..services import audio, image

from . import tasks

async def save_file(file):
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        file_path = temp_file.name

    return file_path


async def process_audio_task(audio_file : UploadFile, background_tasks : BackgroundTasks):
    audio_file_path = await save_file(audio_file)
    task_id = f"file_{os.path.basename(audio_file_path)}"
    tasks[task_id] = {"status": "pending"}

    background_tasks.add_task(file_processor, task_id, audio_file_path, audio.transcribe_audio)
    return task_id


async def process_image_task(image_file : UploadFile, background_tasks : BackgroundTasks):
    image_file_path = await save_file(image_file)
    task_id = f"file_{os.path.basename(image_file_path)}"
    tasks[task_id] = {"status": "pending"}

    background_tasks.add_task(file_processor, task_id, image_file_path, image.extract_text_from_image)
    return task_id




async def file_processor(task_id: str, file_path: str, processor):
    tasks[task_id]["status"] = "processing"
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, processor, file_path)
        tasks[task_id] = {"status": "completed", "result": result}
        print(f"task: {tasks[task_id]}, finished")
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)