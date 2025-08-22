
import re
from typing import List, Dict, Any

from app.services.text.claim_extraction import FactualClaim
from .claim_extraction import extract_claims

def clean_text(text: str) -> str:
    """
    Remove unwanted characters and excessive whitespace from text.
    """
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    # Replace multiple spaces/newlines with single
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_text(text: str) -> Dict[str, Any]:
    """
    Tokenize text into sentences and key phrases using spaCy if available, else fallback to regex.
    """
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        key_phrases = [chunk.text.strip() for chunk in doc.noun_chunks]
    except Exception:
        # Fallback: split sentences by period, extract noun phrases by regex
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if s.strip()]
        key_phrases = re.findall(r'\b\w+(?: \w+){0,2}\b', text)
    return {
        'sentences': sentences,
        'key_phrases': key_phrases
    }

def ingest_and_parse(text: str) -> Dict[str, Any]:
    """
    Entry point for text ingestion and parsing.
    Cleans and tokenizes the input text.
    """
    cleaned = clean_text(text)
    tokens = tokenize_text(cleaned)

    return {
        'cleaned_text': cleaned,
        'sentences': tokens['sentences'],
        'key_phrases': tokens['key_phrases']
    }

def extract_factual_claims_from_text(text: str) -> List[FactualClaim]:
    """
    Extracts factual claims from the input text using Gemini via LangChain.
    """
    return extract_claims(text)

# Example usage:
# claims = extract_factual_claims_from_text("Your text here.")
# print(claims)