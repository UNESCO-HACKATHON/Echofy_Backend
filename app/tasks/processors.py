import os
import tempfile
import asyncio

from fastapi import BackgroundTasks, UploadFile

from app.services import audio, image

from . import tasks

# Save an uploaded file to a temporary location and return its path
async def save_file(file):  # Save uploaded file to a temp file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        file_path = temp_file.name
    return file_path  # Return path to saved file


# Start an audio processing task in the background and return its task id
async def process_audio_task(audio_file: UploadFile, background_tasks: BackgroundTasks):
    audio_file_path = await save_file(audio_file)  # Save audio file
    task_id = f"file_{os.path.basename(audio_file_path)}"  # Unique task id
    tasks[task_id] = {"status": "pending"}
    background_tasks.add_task(
        file_processor, task_id, audio_file_path, audio.transcribe_audio
    )  # Start processing
    return task_id


# Start an image processing task in the background and return its task id.
async def process_image_task(image_file: UploadFile, background_tasks: BackgroundTasks):
    image_file_path = await save_file(image_file)  # Save image file
    task_id = f"file_{os.path.basename(image_file_path)}"  # Unique task id
    tasks[task_id] = {"status": "pending"}
    background_tasks.add_task(
        file_processor, task_id, image_file_path, image.extract_text_from_image
    )  # Start processing
    return task_id


# Run the processor on the file and update the task status/result.
async def file_processor(task_id: str, file_path: str, processor):
    tasks[task_id]["status"] = "processing"  # Mark as processing
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, processor, file_path
        )  # Run processor in thread
        tasks[task_id] = {"status": "completed", "result": result}  # Save result
        print(f"task: {tasks[task_id]}, finished")
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}  # Save error
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)  # Clean up temp file
