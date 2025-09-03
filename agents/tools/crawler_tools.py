import arxiv
from backend.app.services.db_service import *
from langchain_core.tools import tool
from typing import List, Dict
from langchain_core.runnables import RunnableConfig
import requests
@tool
def get_user_interests(config:RunnableConfig) -> Dict:
    """
    Retrieve a user's topic preferences from the database.
    Returns:
        dict: A dictionary containing a list of categories the user is interested in.
        Format:
        {
            "categories": [
                {"category": <category_name>, "weight": <preference_weight>},
                ...
            ]
        }
    """
    
    try:
        user_id = config["configurable"]["user_id"]
        with get_db() as db:
            prefs = get_user_preferences(db, user_id=str(user_id))
            results = {"categories": []}
            
            if not prefs:
                return {"categories": [], "message": "No preferences found for user"}
            
            for r in prefs:
                results["categories"].append({"category": r.category, "weight": r.weight})
      
        return results
            
    except Exception as e:
        print(f"Error retrieving user interests: {str(e)}")
        return {"categories": [], "error": f"Database error: {str(e)}"}

@tool
def fetch_recent_papers(query: str, max_results: str = "10") -> List[Dict]:
    """
    Tool: Fetch recent papers from arXiv based on a search query.
    
    Args:
        query (str): Search keywords for arXiv.
        max_results (str): Number of papers to retrieve (default: '10').
        
    Returns:
        list[dict]: List of paper metadata dictionaries containing:
        - id: arXiv entry ID
        - title: Paper title
        - authors: List of author names
        - summary: Paper abstract
        - published: Publication date
        - updated: Last updated date
        - pdf_url: Direct link to PDF
        - primary_category: Main arXiv category
        - categories: All relevant categories
    """
    if not query or not query.strip():
        return [{"error": "Query cannot be empty"}]
    
    try:
        # print(f"Fetching papers for query: '{query}' with max_results: {int(max_results)}")
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=int(max_results),
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = []
        count = 0
        for result in client.results(search):
            count += 1
            paper_data = {
                "id": result.entry_id,
                "title": result.title.replace('\n', ' ').strip(),
                "authors": [author.name for author in result.authors],
                "summary": result.summary , 
                "published": result.published.isoformat() if result.published else None,
                "updated": result.updated.isoformat() if result.updated else None,
                "pdf_url": result.pdf_url,
            }
            results.append(paper_data)
            
        # print(f"Successfully fetched {len(results)} papers")
        return results
        
    except Exception as e:
        error_msg = f"Failed to fetch papers: {str(e)}"
        print(error_msg)
        return [{"error": error_msg}]
    
    