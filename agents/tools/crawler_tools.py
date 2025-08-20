import arxiv
from backend.app.services.db_service import *
from langchain.tools import tool
from typing import List, Dict
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import ensure_config

@tool
def get_user_interests(config: RunnableConfig ) -> dict:
    """
    Tool: Retrieve a user's preferences as a JSON-serializable dict.
    Note: user_id is automatically provided from the runtime configuration (LangGraph state).
    """
    # Ensure we have a valid config
    config = ensure_config(config)
    
    # Access user_id from the configuration
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return {"topics": [], "categories": []}
    
    with get_db() as db:
        prefs = get_user_preferences(db, user_id=user_id)
        if not prefs:
            return {"topics": [], "categories": []}
        
        return {
            "topics": prefs.topics or [],
            "categories": prefs.categories or []
        }

@tool
def fetch_recent_papers(query: str, max_results: int = 5) -> List[Dict]:
    """
    Tool: Fetch recent papers from arXiv based on a search query.
    
    Args:
        query (str): Search keywords for arXiv.
        max_results (int): Number of papers to retrieve (default: 30).
    
    Returns:
        list[dict]: List of paper metadata dictionaries containing:
        - title
        - authors
        - summary
        - published
        - updated
        - pdf_url
        - primary_category
        - categories
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = []
        for result in client.results(search):
            results.append({
                "id" : result.entry_id , 
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published": result.published.isoformat() if result.published else None,
                "updated": result.updated.isoformat() if result.updated else None,
                "pdf_url": result.pdf_url,
                "primary_category": result.primary_category,
                "categories": result.categories
            })
        
        return results
    
    except Exception as e:
        # Return empty list with error info for debugging
        return [{"error": f"Failed to fetch papers: {str(e)}"}]
    
    
