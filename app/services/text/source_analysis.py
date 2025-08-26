import os
import spacy
from typing import List, Optional
from pydantic import BaseModel
from transformers import pipeline
import google.generativeai as genai

# --- Pydantic Models ---
class NamedEntity(BaseModel):
    text: str
    label: str
    source: str

class SourceAnalysisResult(BaseModel):
    credibility_score: float
    bias_assessment: str # This will now be the dynamic AI-generated note
    notes: str

# --- Model Loading ---
try:
    nlp_spacy = spacy.load('en_core_web_sm')
    ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        llm = genai.GenerativeModel('gemini-1.5-flash')
    else:
        llm = None
except Exception as e:
    nlp_spacy = None
    ner_pipeline = None
    llm = None
    print(f"Warning: A model could not be loaded in source_analysis. Analysis will be affected. Error: {e}")

# --- Mock Database ---
BIASED_SOURCES = {
    "daily-mail.com": "Right-leaning, potential for sensationalism",
    "breitbart.com": "Far-right, known for strong political bias",
    "theguardian.com": "Left-leaning, generally reliable but with a clear perspective"
}

# --- Analysis Functions ---
def generate_dynamic_assessment(source_notes: str, credibility_score: float) -> str:
    """Uses Gemini to generate a dynamic assessment of source bias."""
    if not llm:
        return source_notes # Fallback to static notes

    prompt = f"""
    Based on the following information about a news source, provide a brief, one-sentence analysis of its potential bias and reliability.

    Information:
    - Note: "{source_notes}"
    - Calculated Credibility Score: {credibility_score:.2f} (out of 1.0)

    Example analysis: "This source is on a watchlist for right-leaning bias, which is reflected in its moderate credibility score."
    Example analysis: "This source is not on any watchlist and has a high credibility score, suggesting it is generally reliable."

    Based on the information, your one-sentence analysis is:
    """
    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating dynamic source assessment: {e}")
        return "AI-generated assessment is currently unavailable."

def extract_entities(text: str) -> List[NamedEntity]:
    """Extracts named entities using both spaCy and a Hugging Face transformer model."""
    if not nlp_spacy or not ner_pipeline:
        return []
    # ... (rest of the function remains the same)
    entities = []
    doc = nlp_spacy(text)
    for ent in doc.ents:
        entities.append(NamedEntity(text=ent.text, label=ent.label_, source='spacy'))
    transformer_results = ner_pipeline(text)
    for result in transformer_results:
        if not result['word'].startswith('##'):
             entities.append(NamedEntity(text=result['word'], label=result['entity_group'], source='transformers'))
    unique_entities = { (e.text.lower(), e.label) : e for e in entities }
    return list(unique_entities.values())

from urllib.parse import urlparse
# ... existing code ...
def analyze_source(url: Optional[str] = None, author: Optional[str] = None) -> SourceAnalysisResult:
    """Analyzes the source of the text for credibility and bias."""
    credibility_score = 0.8
    notes = "Source not found in the watchlist."

    if url:
        try:
            domain = urlparse(url).netloc
            if domain and domain in BIASED_SOURCES:
                credibility_score = 0.5
                notes = f"Source domain '{domain}' is on a watchlist: {BIASED_SOURCES[domain]}"
        except Exception:
            # If URL parsing fails, we just treat it as if no URL was provided
            pass

    # Generate the dynamic assessment using the AI
    dynamic_assessment = generate_dynamic_assessment(notes, credibility_score)

    return SourceAnalysisResult(
        credibility_score=credibility_score,
        bias_assessment=dynamic_assessment,
        notes=notes # Keep the original notes for reference
    )
