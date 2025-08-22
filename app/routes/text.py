from fastapi import APIRouter

from app.services.text.entry import router as text_router

router = APIRouter()

router.include_router(text_router)