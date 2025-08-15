from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.api.v1.models import analysisModel

from app.services.analysis_service import perform_analysis

router = APIRouter()

@router.post(
    "/analyze",
    response_model=analysisModel.AnalysisResponse,
    summary="Analyze Text Content",
    description="Receives a piece of text and analyzes it for potential misinformation or AI-generation markers."
)
async def analyze_content(request: analysisModel.AnalysisRequest):
    """
    This endpoint takes text content and uses the analysis service to evaluate it.

    - **request**: The request body, which must match the `AnalysisRequest` Pydantic model.
    """
    try:
        # The API endpoint's job is simple:
        # 1, Validate the incoming request
        # 2, Pass the relevant data to the service layer
        # 3, Return the result from the service layer
        analysis_result = perform_analysis(request.content)
        return analysis_result

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        print(f"An Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))