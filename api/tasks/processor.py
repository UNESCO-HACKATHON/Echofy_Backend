import os
import tempfile
import asyncio
from services.audio import transcribe_audio

from . import tasks

async def process_audio_task(audio_file, background_tasks):
    suffix = os.path.splitext(audio_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await audio_file.read()
        temp_file.write(content)
        audio_file_path = temp_file.name

    task_id = f"audio_{os.path.basename(audio_file_path)}"
    tasks[task_id] = {"status": "pending", "result": None}

    background_tasks.add_task(file_processor, task_id, audio_file_path, transcribe_audio)
    return task_id


async def file_processor(task_id: str, file_path: str, processor):
    tasks[task_id]["status"] = "processing"
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, processor, file_path)
        tasks[task_id] = {"status": "completed", "result": result}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)