import os
from typing import List, Dict
from pydantic import BaseModel
import google.generativeai as genai

# Import the actual data models from other modules
from .sentiment_analysis import SentimentResult
from .source_analysis import SourceAnalysisResult

# This model defines the structure needed for verification results
class ClaimVerification(BaseModel):
    claim: str
    final_assessment: str  # 'SUPPORTED', 'CONTRADICTED', 'UNCERTAIN'

# --- Final Output Model ---
class TrustScoreResponse(BaseModel):
    trust_score: float
    summary: str # This will be the dynamic AI-generated summary
    factors: Dict[str, str]

# --- Model Loading ---
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        llm = genai.GenerativeModel('gemini-1.5-flash')
    else:
        llm = None
except Exception as e:
    llm = None
    print(f"Warning: Gemini model could not be loaded in score_aggregation. Summaries will be static. Error: {e}")

# --- Aggregation Logic ---
WEIGHTS = {
    'verification': 0.6,
    'sentiment': 0.2,
    'source_credibility': 0.2
}

def generate_dynamic_summary(final_score: float, factors: Dict[str, str]) -> str:
    """Uses Gemini to generate a dynamic summary based on the final score and factors."""
    if not llm:
        # Fallback to static summary
        if final_score > 0.7:
            return "The text appears to be generally trustworthy, with most claims supported by evidence and neutral language."
        elif final_score > 0.4:
            return "Exercise caution. While some claims are supported, there are indicators of potential bias or unverified information."
        else:
            return "High skepticism advised. The text contains significant contradictions, biased language, or originates from a source with low credibility."

    prompt = f"""
    Analyze the following trust score and contributing factors to provide a final, one-sentence summary for the user.

    Data:
    - Final Trust Score: {final_score:.2f} (out of 1.0)
    - Verification Factor: "{factors.get('verification', 'N/A')}"
    - Sentiment Factor: "{factors.get('sentiment', 'N/A')}"
    - Source Credibility Factor: "{factors.get('source_credibility', 'N/A')}"

    Example summary: "This text is moderately trustworthy; while the source is credible, the language is highly emotional and some claims could not be verified."
    Example summary: "This text is highly trustworthy, with verified claims from a credible source and neutral language."

    Based on the data, your one-sentence summary is:
    """
    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating dynamic summary: {e}")
        return "AI-generated summary is currently unavailable."

def aggregate_scores(
    claim_verifications: List[ClaimVerification],
    sentiment_result: SentimentResult,
    source_analysis: SourceAnalysisResult
) -> TrustScoreResponse:
    """Aggregates scores from all analysis modules to produce a final trust score."""
    factors = {}
    
    # 1. Calculate Verification Score
    verification_score = 0.0
    if claim_verifications:
        supported_count = sum(1 for v in claim_verifications if v.final_assessment == 'SUPPORTED')
        contradicted_count = sum(1 for v in claim_verifications if v.final_assessment == 'CONTRADICTED')
        verification_score = max(0, (supported_count - (contradicted_count * 2))) / len(claim_verifications)
        factors['verification'] = f"{supported_count} supported, {contradicted_count} contradicted claims."
    else:
        factors['verification'] = "No claims were verified."

    # 2. Calculate Sentiment Score
    sentiment_polarity = abs(sentiment_result.vader_scores.get('compound', 0.0))
    sentiment_score = 1 - sentiment_polarity
    factors['sentiment'] = f"Sentiment: {sentiment_result.notes}"

    # 3. Get Source Credibility Score
    source_score = source_analysis.credibility_score
    factors['source_credibility'] = f"Source: {source_analysis.bias_assessment}"

    # 4. Calculate Final Weighted Score
    final_score = (
        (verification_score * WEIGHTS['verification']) +
        (sentiment_score * WEIGHTS['sentiment']) +
        (source_score * WEIGHTS['source_credibility'])
    )
    final_score = max(0, min(1, final_score))

    # 5. Generate Dynamic Summary
    summary = generate_dynamic_summary(final_score, factors)

    return TrustScoreResponse(
        trust_score=final_score,
        summary=summary,
        factors=factors
    )
