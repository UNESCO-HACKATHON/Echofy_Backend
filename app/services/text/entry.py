from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

# Import all the analysis modules
from .parser import ingest_and_parse
from .claim_extraction import extract_claims, FactualClaim
from .source_analysis import analyze_source, extract_entities
from .verification import verify_claim
from .sentiment_analysis import analyze_sentiment_and_tone
from .score_aggregation import aggregate_scores, ClaimVerification

router = APIRouter(
    prefix="/text",
    tags=["Text Analysis"],
)

# --- Pydantic Models for API Request and Response ---

class AnalysisRequest(BaseModel):
    text: str
    url: Optional[str] = None

class ClaimBreakdown(BaseModel):
    claim: str
    status: str
    supporting_sources: List[str] = []
    reason: Optional[str] = None

class SourceBreakdown(BaseModel):
    publisher: Optional[str] = None
    credibility_score: float
    potential_bias: str

class SentimentBreakdown(BaseModel):
    score: float
    tone: str

class Breakdown(BaseModel):
    claim_extraction: List[ClaimBreakdown]
    source_analysis: SourceBreakdown
    sentiment_analysis: SentimentBreakdown

class AnalysisResponse(BaseModel):
    trust_score: float
    summary: str
    breakdown: Breakdown
    flags: List[str] = []

# --- API Endpoint ---

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text_content(request: AnalysisRequest):
    """
    Run a full analysis on a piece of text to generate a trust score.
    """
    try:
        # 1. Ingest and Parse Text
        parsed_text = ingest_and_parse(request.text)
        cleaned_text = parsed_text['cleaned_text']

        # 2. Extract Factual Claims
        claims = extract_claims(cleaned_text)

        # 3. Analyze Source and Sentiment
        source_analysis_result = analyze_source(url=request.url)
        sentiment_result = analyze_sentiment_and_tone(cleaned_text)

        # 4. Verify each claim and build breakdown
        claim_breakdowns: List[ClaimBreakdown] = []
        claim_verifications_for_scoring: List[ClaimVerification] = []
        for claim_model in claims:
            verification_response = verify_claim(claim_model.text)
            
            status = "UNCERTAIN"
            if "SUPPORTED" in verification_response.upper():
                status = "SUPPORTED"
            elif "CONTRADICTED" in verification_response.upper():
                status = "CONTRADICTED"

            claim_breakdowns.append(ClaimBreakdown(
                claim=claim_model.text,
                status=status,
                reason=verification_response
            ))
            # Create the correct Pydantic model for scoring
            claim_verifications_for_scoring.append(
                ClaimVerification(claim=claim_model.text, final_assessment=status)
            )

        # 5. Aggregate final score
        final_score_response = aggregate_scores(
            claim_verifications=claim_verifications_for_scoring,
            sentiment_result=sentiment_result,
            source_analysis=source_analysis_result
        )

        # 6. Assemble the final response
        response_breakdown = Breakdown(
            claim_extraction=claim_breakdowns,
            source_analysis=SourceBreakdown(
                publisher=request.url.split('/')[2] if request.url else "Unknown",
                credibility_score=source_analysis_result.credibility_score,
                potential_bias=source_analysis_result.bias_assessment
            ),
            sentiment_analysis=SentimentBreakdown(
                score=sentiment_result.vader_scores.get('compound', 0.0),
                tone=sentiment_result.overall_sentiment
            )
        )

        return AnalysisResponse(
            trust_score=final_score_response.trust_score,
            summary=final_score_response.summary,
            breakdown=response_breakdown,
            flags=[sentiment_result.notes] if "Warning" in sentiment_result.notes else []
        )

    except Exception as e:
        # Catch-all for any errors during the complex pipeline
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
