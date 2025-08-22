from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import routes

app = FastAPI(
    title="Media and Information Literacy (MIL) Content Analysis API",
    description="An API to analyze content for potential misinformation or AI generation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows specific origins to make requests
    allow_credentials=True,  # Allows cookies and authentication headers
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all HTTP headers
)

app.include_router(routes.router, prefix="/api", tags=["Content Analysis"])


@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple welcome message to confirm the API is up and running.
    """

    return {"message": "Welcome to the MIL Content Analysis API!"}
