
import os
from typing import List
from pydantic import BaseModel
import google.generativeai as genai

# Load Gemini API key from environment and configure the library
GEMINI_API_KEY = os.getenv("GEMINI_API")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini LLM
llm = genai.GenerativeModel('gemini-1.5-flash')


# Detailed prompt for claim extraction
CLAIM_PROMPT = """
You are an expert fact-checking assistant. Your task is to read the provided text and extract all statements that are verifiable factual claims. A factual claim is a statement that can be checked for accuracy using external sources, such as dates, numbers, events, names, or specific assertions about reality. Do not include opinions, emotional language, generalizations, or subjective statements.

Instructions:
- List only the factual claims, one per line.
- Exclude any statements that are opinions, predictions, or vague descriptions.
- If a sentence contains both factual and non-factual content, extract only the factual part.
- Do not include any explanation or commentary, just the claims.

Text to analyze:
{text}
"""

# Pydantic model for a factual claim
class FactualClaim(BaseModel):
    text: str

def extract_claims(text: str) -> List[FactualClaim]:
    """
    Uses the google-generativeai library directly to extract factual claims from text.
    Returns a list of FactualClaim models.
    """
    # The prompt is now just a formatted string, not a LangChain object
    full_prompt = CLAIM_PROMPT.format(text=text)
    
    try:
        response = llm.generate_content(full_prompt)
        claims = [line.strip('- ').strip() for line in response.text.split('\n') if line.strip()]
        return [FactualClaim(text=claim) for claim in claims]
    except Exception as e:
        print(f"An error occurred during claim extraction: {e}")
        # In case of an API error, return an empty list
        return []
