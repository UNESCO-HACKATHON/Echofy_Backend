
from fastapi import APIRouter, UploadFile, HTTPException
from app.services import image
from app.services.text.parser import ingest_and_parse
from app.services.text.claim_extraction import extract_claims
from app.services.text.verification import verify_claim
from app.services.text.sentiment_analysis import analyze_sentiment_and_tone
from app.services.text.score_aggregation import aggregate_scores, ClaimVerification
from app.services.text.entry import AnalysisResponse, Breakdown, ClaimBreakdown, SourceBreakdown, SentimentBreakdown

router = APIRouter()

@router.post("/analyze/image/", response_model=AnalysisResponse)
async def analyze_image(image_file: UploadFile):
    """
    Accepts an image file, extracts text, and runs the text analysis pipeline.
    Returns the same output as the text/audio endpoint.
    """
    try:
        # 1. Extract text from image
        import tempfile, os
        suffix = os.path.splitext(image_file.filename)[1] if image_file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await image_file.read()
            temp_file.write(content)
            image_file_path = temp_file.name
        extracted_text = image.extract_text_from_image(image_file_path)
        os.remove(image_file_path)

        # 2. Ingest and Parse Text
        parsed_text = ingest_and_parse(extracted_text or "")
        cleaned_text = parsed_text['cleaned_text']

        # 3. Extract Factual Claims
        claims = extract_claims(cleaned_text)

        # 4. Analyze Sentiment
        sentiment_result = analyze_sentiment_and_tone(cleaned_text)

        # 5. Verify each claim and build breakdown
        claim_breakdowns = []
        claim_verifications_for_scoring = []
        for claim_model in claims:
            verification_result = verify_claim(claim_model.text)
            
            claim_breakdowns.append(ClaimBreakdown(
                claim=verification_result.claim,
                status=verification_result.final_assessment,
                reason=verification_result.reasoning,
                corrective_statement=verification_result.corrective_statement,
                supporting_evidence=verification_result.supporting_evidence,
                sources=verification_result.sources
            ))
            # Create the correct Pydantic model for scoring
            claim_verifications_for_scoring.append(
                ClaimVerification(claim=verification_result.claim, final_assessment=verification_result.final_assessment)
            )

        # 6. Create dummy source analysis
        source_analysis_result = SourceBreakdown(
            publisher="Unknown",
            credibility_score=0.0,
            potential_bias="Unknown"
        )

        # 7. Aggregate final score
        # Create a proper SourceAnalysisResult dummy object for aggregate_scores
        from app.services.text.source_analysis import SourceAnalysisResult
        dummy_source = SourceAnalysisResult(
            credibility_score=0.0,
            bias_assessment="Unknown",
            notes=""
        )
        final_score_response = aggregate_scores(
            claim_verifications=claim_verifications_for_scoring,
            sentiment_result=sentiment_result,
            source_analysis=dummy_source
        )

        # 8. Assemble the final response
        response_breakdown = Breakdown(
            claim_extraction=claim_breakdowns,
            source_analysis=source_analysis_result,
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
        raise HTTPException(status_code=500, detail=str(e))