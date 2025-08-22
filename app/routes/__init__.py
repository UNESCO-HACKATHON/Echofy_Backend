from fastapi  import APIRouter
from . import audio, image, tasks, text

router = APIRouter()

router.include_router(audio.router)
router.include_router(image.router)
router.include_router(text.router)
router.include_router(tasks.router)

# Removed duplicate '/analyze/image/' endpoint to avoid route conflict.

@router.post("/analyze/video/")
async def analyze_video(content : str):
    # Placeholder for content analysis logic
    return {"message": "Content analyzed", "content": content}