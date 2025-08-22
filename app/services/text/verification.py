import os
import requests
from typing import List, Optional
from pydantic import BaseModel
import google.generativeai as genai
from newsapi import NewsApiClient
from dotenv import load_dotenv
from tavily import TavilyClient
import wikipedia
import praw

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
genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel('gemini-1.5-flash')

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
        return "### Serper Web Search Results:\n" + "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in results[:3]])
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
        return "### Tavily Web Search Results:\n" + "\n".join([f"- {r.get('title')}: {r.get('content')}" for r in results[:3]])
    except Exception as e:
        return f"Error with Tavily search: {e}"

def search_wikipedia(query: str) -> str:
    """Searches Wikipedia for a given query and returns the page summary."""
    try:
        # To avoid ambiguity, get the page title first
        page_title = wikipedia.search(query, results=1)
        if not page_title:
            return "### Wikipedia Results:\nNo page found for this query."
        page = wikipedia.page(page_title[0], auto_suggest=False)
        return f"### Wikipedia Results for '{page.title}':\n{page.summary}"
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
        return "### NewsAPI.org Results:\n" + "\n".join([f"- {a['title']}: {a.get('description', '')}" for a in articles[:3]])
    except Exception as e:
        return f"Error with NewsAPI.org search: {e}"

def search_newsdata_io(query: str) -> str:
    """Searches for news articles using Newsdata.io."""
    if not NEWSDATA_IO_KEY:
        return "Newsdata.io key not configured."
    try:
        response = requests.get(
            f"https://newsdata.io/api/1/news?apikey={NEWSDATA_IO_KEY}&q={query}&language=en"
        )
        response.raise_for_status()
        articles = response.json().get('results', [])
        return "### Newsdata.io Results:\n" + "\n".join([f"- {a['title']}: {a.get('description', '')}" for a in articles[:3]])
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
        return "### Google Fact Check Results:\n" + "\n".join([f"- Claim: {c.get('text', '')} - Verdict: {c.get('claimReview', [{}])[0].get('textualRating', 'N/A')}" for c in claims[:3]])
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
        
        all_results = []
        subreddit_list = "+".join(selected_subreddits)
        
        # Search across the selected subreddits
        search_results = reddit.subreddit(subreddit_list).search(query, limit=3, sort='relevance')

        for submission in search_results:
            submission.comments.replace_more(limit=0) # Load top-level comments
            top_comment = submission.comments[0].body if submission.comments else "No comments."
            all_results.append(f"- Post Title: {submission.title}\n  Top Comment: {top_comment[:200]}...")

        if not all_results:
            return f"### Reddit Results in r/{subreddit_list}:\nNo relevant posts found."

        return f"### Reddit Results in r/{subreddit_list}:\n" + "\n".join(all_results)

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
    return "\n\n".join(results)

def verify_claim(claim: str) -> str:
    """
    Uses the google-generativeai library and external search tools to verify a factual claim.
    """
    search_results = search_all_sources(claim)
    
    prompt = f"""
    Your task is to verify the following claim based on the provided search results.

    Claim: "{claim}"

    Search Results:
    ---
    {search_results}
    ---

    Based on the search results, provide a final assessment: SUPPORTED, CONTRADICTED, or UNCERTAIN.
    Explain your reasoning based on the information you found in the search results.
    """
    
    try:
        response = llm.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred during verification: {e}"

