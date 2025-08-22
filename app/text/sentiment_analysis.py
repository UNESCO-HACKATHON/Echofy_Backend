import os
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline
from pydantic import BaseModel
from typing import Dict
import google.generativeai as genai

# --- Pydantic Model for Structured Output ---

class SentimentResult(BaseModel):
    vader_scores: Dict[str, float]
    transformer_label: str
    transformer_score: float
    overall_sentiment: str
    notes: str

# --- Model Loading ---

# Download VADER lexicon if not already present
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

# Load models once to be reused
try:
    vader_analyzer = SentimentIntensityAnalyzer()
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    
    # Initialize Gemini for dynamic notes
    GEMINI_API_KEY = os.getenv("GEMINI_API")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        llm = genai.GenerativeModel('gemini-1.5-flash')
    else:
        llm = None
except Exception as e:
    vader_analyzer = None
    sentiment_pipeline = None
    llm = None
    print(f"Warning: A model could not be loaded. Analysis will be affected. Error: {e}")

# --- Analysis Functions ---

def generate_dynamic_notes(vader_scores: Dict[str, float], transformer_label: str) -> str:
    """
    Uses Gemini to generate a dynamic explanation for the sentiment scores.
    """
    if not llm:
        # Fallback to static notes if the LLM is not available
        compound_score = vader_scores.get('compound', 0.0)
        if abs(compound_score) > 0.7:
            return "Warning: Text has a very strong sentiment polarity, which could be indicative of manipulative or biased language."
        elif vader_scores.get('neu', 1.0) < 0.5:
            return "Note: Text is highly emotional with low neutrality."
        return "No specific manipulative language detected."

    prompt = f"""
    Analyze the following sentiment scores from a piece of text and provide a brief, one-sentence explanation of the tone.
    If the sentiment is very strong (e.g., VADER compound score > 0.7 or < -0.7) or not very neutral, mention that this could indicate biased or manipulative language.

    Scores:
    - VADER Compound Score: {vader_scores.get('compound', 0.0):.2f} (A single score from -1 for negative to +1 for positive)
    - Transformer Classification: {transformer_label}

    Example analysis: "The text has a strong negative polarity, which may indicate biased language."
    Example analysis: "The text is mostly neutral but leans slightly positive."

    Based on the scores, your one-sentence analysis is:
    """
    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating dynamic sentiment notes: {e}")
        return "AI-generated notes are currently unavailable."

def analyze_sentiment_and_tone(text: str) -> SentimentResult:
    """
    Analyzes the sentiment and tone of the text using VADER and a Hugging Face transformer.
    Detects manipulative or biased language based on sentiment scores.
    """
    if not vader_analyzer or not sentiment_pipeline:
        return SentimentResult(
            vader_scores={'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compound': 0.0},
            transformer_label="UNAVAILABLE",
            transformer_score=0.0,
            overall_sentiment="UNKNOWN",
            notes="Sentiment models could not be loaded."
        )

    # 1. VADER Analysis (good for polarity and intensity)
    vader_scores = vader_analyzer.polarity_scores(text)
    compound_score = vader_scores['compound']

    # 2. Hugging Face Transformer Analysis (good for classification)
    transformer_result = sentiment_pipeline(text)[0]
    transformer_label = transformer_result['label']
    transformer_score = transformer_result['score']

    # 3. Synthesize results for overall sentiment
    overall_sentiment = "NEUTRAL"
    if compound_score > 0.05 and transformer_label == 'POSITIVE':
        overall_sentiment = "POSITIVE"
    elif compound_score < -0.05 and transformer_label == 'NEGATIVE':
        overall_sentiment = "NEGATIVE"

    # 4. Generate dynamic notes based on the scores
    notes = generate_dynamic_notes(vader_scores, transformer_label)

    return SentimentResult(
        vader_scores=vader_scores,
        transformer_label=transformer_label,
        transformer_score=transformer_score,
        overall_sentiment=overall_sentiment,
        notes=notes
    )
