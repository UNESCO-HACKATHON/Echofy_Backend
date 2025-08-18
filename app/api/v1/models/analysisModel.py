from pydantic import BaseModel, Field
# this file defines the data structures for API requests and responses

class AnalysisRequest(BaseModel):
    """
    Defines the structure for a request to the /analyze endpoint.
    """
    content: str = Field(
        ..., # this means the field is required
        title = "Content to Analyze",
        description="The text content (e.g., article, video title, transcribed audio) to be analyzed.",
        min_length=10,
        max_length=10000,
        examples=["This is a sample content to analyze."]
    )
    

class AnalysisResponse(BaseModel):
    """
    Defines the structure for the response from the /analyze endpoint.
    """
    is_potentially_misleading: bool = Field (
        ...,
        title="Misleading Content Flag",
        description="True if the content is flagged as potentially misleading or AI-generated"
    )
    
    confidence_score: float = Field(
        ...,
        title="Confidence Score",
        description="A score from 0.0 to 1.0 indicating the model's confidence in its assessment.",
        ge=0.0,
        le=1.0
    )

    explanation: str = Field(
        ...,
        title="Explanation",
        description="A brief explanation of why the content was flagged (e.g 'Uses emotionally charged langauge')"
    )