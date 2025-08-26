import os
import requests
import wikipedia
import praw
import json
from typing import List, Optional, Dict
from pydantic import BaseModel
from newsapi import NewsApiClient
from dotenv import load_dotenv
from tavily import TavilyClient
import google.generativeai as genai
from urllib.parse import quote_plus, urlparse

load_dotenv()

# --- Pydantic Models for Structured Output ---

class VerificationResult(BaseModel):
    source: str
    supports: str  # 'SUPPORTED', 'CONTRADICTED', 'NEUTRAL'
    summary: str
    url: Optional[str] = None

class ClaimVerification(BaseModel):
    claim: str
    results: List[VerificationResult]
    final_assessment: str
    reasoning: str
    corrective_statement: Optional[str] = None
    supporting_evidence: Optional[str] = None
    sources: List[Dict[str, str]] = []

# --- API Key Loading ---

SERPER_API_KEY = os.getenv("SERPER_API")
NEWSAPI_ORG_KEY = os.getenv("NEWSAPI_ORG")
NEWSDATA_IO_KEY = os.getenv("NEWSDATA_IO")
GOOGLE_FACT_CHECK_KEY = os.getenv("GOOGLE_FACT")
GEMINI_API_KEY = os.getenv("GEMINI_API")
TAVILY_API_KEY = os.getenv("TAVILY_API")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET_KEY = os.getenv("REDDIT_SECRET_KEY")

# Configure the Gemini client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    llm = genai.GenerativeModel('gemini-1.5-flash')
else:
    llm = None

# --- Verification Tools ---

def search_serper(query: str) -> str:
    """Performs a web search using Serper API and returns the top results."""
    if not SERPER_API_KEY:
        return "Serper API key not configured."
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            json={"q": query},
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        )
        response.raise_for_status()
        results = response.json().get('organic', [])
        return "### Serper Web Search Results:\n" + "\n".join([f"- {r.get('title')}: {r.get('snippet')} (Source: {r.get('link')})" for r in results[:3]])
    except Exception as e:
        return f"Error with Serper search: {e}"

def search_tavily(query: str) -> str:
    """Performs a web search using Tavily API and returns the top results."""
    if not TAVILY_API_KEY:
        return "Tavily API key not configured."
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        response = tavily.search(query=query, search_depth="advanced")
        results = response['results']
        return "### Tavily Web Search Results:\n" + "\n".join([f"- {r.get('title')}: {r.get('content')} (Source: {r.get('url')})" for r in results[:3]])
    except Exception as e:
        return f"Error with Tavily search: {e}"

def search_wikipedia(query: str) -> str:
    """Searches Wikipedia for a given query and returns the page summary."""
    try:
        page_titles = wikipedia.search(query, results=1)
        if not page_titles:
            return f"### Wikipedia Results:\nNo page found for '{query}'."
        page = wikipedia.page(page_titles[0], auto_suggest=False)
        return f"### Wikipedia Results for '{page.title}':\n{page.summary} (Source: {page.url})"
    except wikipedia.exceptions.PageError:
        return f"### Wikipedia Results:\nNo page found for '{query}'."
    except wikipedia.exceptions.DisambiguationError as e:
        return f"### Wikipedia Results:\nAmbiguous query. Options: {e.options[:5]}"
    except Exception as e:
        return f"Error with Wikipedia search: {e}"


def search_newsapi_org(query: str) -> str:
    """Searches for news articles using NewsAPI.org."""
    if not NEWSAPI_ORG_KEY:
        return "NewsAPI.org key not configured."
    try:
        newsapi = NewsApiClient(api_key=NEWSAPI_ORG_KEY)
        articles = newsapi.get_everything(q=query, language='en', sort_by='relevancy')['articles']
        return "### NewsAPI.org Results:\n" + "\n".join([f"- {a['title']}: {a.get('description', '')} (Source: {a.get('url')})" for a in articles[:3]])
    except Exception as e:
        return f"Error with NewsAPI.org search: {e}"

def search_newsdata_io(query: str) -> str:
    """Searches for news articles using Newsdata.io."""
    if not NEWSDATA_IO_KEY:
        return "Newsdata.io key not configured."
    try:
        safe_query = quote_plus(query)
        response = requests.get(
            f"https://newsdata.io/api/1/news?apikey={NEWSDATA_IO_KEY}&q={safe_query}&language=en"
        )
        response.raise_for_status()
        articles = response.json().get('results', [])
        return "### Newsdata.io Results:\n" + "\n".join([f"- {a['title']}: {a.get('description', '')} (Source: {a.get('link')})" for a in articles[:3]])
    except Exception as e:
        return f"Error with Newsdata.io search: {e}"

def search_google_fact_check(query: str) -> str:
    """Searches the Google Fact Check Tools API."""
    if not GOOGLE_FACT_CHECK_KEY:
        return "Google Fact Check API key not configured."
    try:
        url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={query}&key={GOOGLE_FACT_CHECK_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        claims = response.json().get('claims', [])
        if not claims:
            return "### Google Fact Check Results:\nNo fact checks found."
        return "### Google Fact Check Results:\n" + "\n".join([f"- Claim: {c.get('text', '')} - Verdict: {c.get('claimReview', [{}])[0].get('textualRating', 'N/A')} (Source: {c.get('claimReview', [{}])[0].get('url')})" for c in claims[:3]])
    except Exception as e:
        return f"Error with Google Fact Check API: {e}"

def search_reddit(query: str) -> str:
    """
    Selects relevant subreddits based on the query and searches for discussions.
    """
    if not REDDIT_CLIENT_ID or not REDDIT_SECRET_KEY:
        return "Reddit API credentials not configured."

    # A mapping of trusted subreddits to keywords
    subreddit_map = {
        'AskHistorians': ['history', 'war', 'ancient', 'historical'],
        'AskScience': ['science', 'biology', 'physics', 'chemistry', 'research'],
        'ChangeMyView': ['opinion', 'view', 'belief', 'perspective'],
        'NeutralPolitics': ['politics', 'government', 'election', 'policy'],
        'Skeptic': ['debunk', 'pseudoscience', 'misinformation', 'hoax'],
        'OutOfTheLoop': ['trending', 'viral', 'what is', 'happened'],
        'WorldNews': ['world', 'international', 'global', 'country'],
        'News': ['news', 'current events', 'breaking'],
        'Factual': ['factual', 'unbiased', 'source-based'],
        'TrueReddit': ['in-depth', 'article', 'long-read'],
        'AskEconomics': ['economics', 'finance', 'market', 'money'],
        'AskPhilosophy': ['philosophy', 'ethics', 'morality', 'meaning'],
        'AskAcademia': ['academic', 'research', 'university', 'study'],
        'BadHistory': ['misconception', 'bad history', 'debunk history'],
        'DataIsBeautiful': ['data', 'visualization', 'statistics', 'chart'],
    }

    # Select relevant subreddits
    query_lower = query.lower()
    selected_subreddits = [
        sub for sub, keywords in subreddit_map.items() 
        if any(keyword in query_lower for keyword in keywords)
    ]

    if not selected_subreddits:
        return "### Reddit Results:\nNo relevant subreddits found for this topic."

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET_KEY,
            user_agent="EchofyFactChecker/1.0"
        )
        
        subreddit_list = "+".join(selected_subreddits)
        
        # Search across the selected subreddits
        search_results = reddit.subreddit(subreddit_list).search(query, limit=3, sort='relevance')
        results_str = "\n".join([f"- {submission.title}: {submission.selftext[:150]}... (Source: https://reddit.com{submission.permalink})" for submission in search_results])
        return f"### Reddit Results from r/{subreddit_list}:\n" + results_str
    except Exception as e:
        return f"Error with Reddit search: {e}"


def search_all_sources(query: str) -> str:
    """Calls all available search tools and aggregates their results."""
    results = [
        search_serper(query),
        search_tavily(query),
        search_wikipedia(query),
        search_newsapi_org(query),
        search_newsdata_io(query),
        search_google_fact_check(query),
        search_reddit(query)
    ]
    return "\n\n".join(filter(None, results))

def generate_alternative_query(claim: str, assessment: str) -> str:
    """Generates an alternative search query using an LLM."""
    if not llm:
        return f"opposite of {claim}" if assessment == 'CONTRADICTED' else f"evidence supporting {claim}"

    if assessment == 'CONTRADICTED':
        prompt = f"The following claim has been contradicted: '{claim}'. Generate a neutral search query to find the correct information or the opposing viewpoint. The query should be objective and suitable for a web search. For example, if the claim is 'The sky is green', a good query would be 'what color is the sky'. Your query is:"
    else: # SUPPORTED
        prompt = f"The following claim has been supported: '{claim}'. Generate a search query to find high-quality, primary sources or strong evidence that further validates this claim. For example, if the claim is 'Water is H2O', a good query would be 'scientific papers on the chemical composition of water'. Your query is:"
    
    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return f"opposite of {claim}" if assessment == 'CONTRADICTED' else f"evidence supporting {claim}"

def analyze_alternative_results(claim: str, search_results: str, assessment: str) -> Dict[str, any]:
    """Analyzes the search results for the alternative query using an LLM."""
    if not llm:
        return {"statement": "Could not analyze alternative results.", "sources": []}

    if assessment == 'CONTRADICTED':
        prompt = f"""
        The original claim was: "{claim}"
        This claim was found to be contradicted. The following search results are from a query trying to find the correct information.
        Your task is to synthesize these results into a single, corrected statement. Also, list the top 3 most reliable source URLs that support this correction.

        Search Results:
        ---
        {search_results}
        ---

        Output the result as a JSON object with two keys: "statement" (the corrected fact) and "sources" (a list of up to 3 URLs).
        Example: {{"statement": "The sky is blue due to Rayleigh scattering.", "sources": ["https://science.nasa.gov/sky-color", "https://www.britannica.com/story/why-is-the-sky-blue"]}}
        """
    else: # SUPPORTED
        prompt = f"""
        The original claim was: "{claim}"
        This claim was found to be supported. The following search results are from a query trying to find more evidence.
        Your task is to synthesize these results into a single sentence that summarizes the supporting evidence. Also, list the top 3 most reliable source URLs that provide this evidence.

        Search Results:
        ---
        {search_results}
        ---

        Output the result as a JSON object with two keys: "statement" (the summary of evidence) and "sources" (a list of up to 3 URLs).
        Example: {{"statement": "Multiple scientific sources confirm water's chemical formula is H2O, based on experiments by Cavendish and Lavoisier.", "sources": ["https://chemistry.libretexts.org/Water", "https://www.nature.com/articles/s41592-021-01145-3"]}}
        """
    
    try:
        response = llm.generate_content(prompt)
        # Clean the response to be valid JSON
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error analyzing alternative results: {e}")
        return {"statement": "AI analysis of alternative results failed.", "sources": []}

def verify_claim(claim: str) -> ClaimVerification:
    """
    Uses the google-generativeai library and external search tools to verify a factual claim,
    and if necessary, finds corrective or supporting information.
    """
    # Initial verification
    initial_search_results = search_all_sources(claim)
    
    prompt = f"""
    Your task is to verify the following claim based on the provided search results.

    Claim: "{claim}"

    Search Results:
    ---
    {initial_search_results}
    ---

    Based ONLY on the search results, provide a final assessment: SUPPORTED, CONTRADICTED, or UNCERTAIN.
    Then, on a new line, provide a brief, one-sentence explanation for your assessment based on the information you found.
    """
    
    try:
        if not llm:
            raise Exception("Gemini LLM not configured.")
        
        response = llm.generate_content(prompt)
        parts = response.text.strip().split('\n')
        final_assessment = parts[0].strip()
        reasoning = parts[1].strip() if len(parts) > 1 else "No reasoning provided."

        corrective_statement = None
        supporting_evidence = None
        sources = []

        # If the claim is not uncertain, perform a second search for more info
        if final_assessment in ['SUPPORTED', 'CONTRADICTED']:
            alternative_query = generate_alternative_query(claim, final_assessment)
            alternative_results_str = search_all_sources(alternative_query)
            analysis = analyze_alternative_results(claim, alternative_results_str, final_assessment)
            
            if final_assessment == 'CONTRADICTED':
                corrective_statement = analysis.get("statement")
            else:
                supporting_evidence = analysis.get("statement")
            
            sources = [{"url": src} for src in analysis.get("sources", [])]

        return ClaimVerification(
            claim=claim,
            results=[], # This is complex to populate, leaving for future enhancement
            final_assessment=final_assessment,
            corrective_statement=corrective_statement,
            supporting_evidence=supporting_evidence,
            sources=sources,
            reasoning=reasoning
        )

    except Exception as e:
        print(f"An error occurred during claim verification: {e}")
        return ClaimVerification(
            claim=claim,
            results=[],
            final_assessment='UNCERTAIN',
            reasoning=f"An error occurred: {e}"
        )

