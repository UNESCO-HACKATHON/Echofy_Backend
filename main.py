from fastapi import FastAPI
from app.api.v1.routes import analysis

app = FastAPI(
    title="Media and Information Literacy (MIL) Content Analysis API",
    description="An API to analyze content for potential misinformation or AI generation.",
    version="1.0.0"
)

app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])


app.get("/", tags=["Root"])
async def read_root():
    """
    A simple welcome message to confirm the API is up and running.
    """
    return {"message": "Welcome to the MIL Content Analysis API!"}