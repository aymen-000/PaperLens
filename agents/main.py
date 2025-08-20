from typing import List, Dict
from agents.system_agents.crawler import call_crawler_agent
from agents.data.embedding import handle_paper_interaction , get_paper_recommendations
from agents.data.vector_db import PaperVectorStore
import uuid
def main(user_id:str):
    # Step 1: Crawl papers
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "user_id": "1",  
            "thread_id": thread_id,
        }
    }
    papers = call_crawler_agent(config=config)  # List[Dict] with keys: id, title, abstract, authors, categories, published, url
    print(f"[INFO] Crawled {len(papers)} papers.")
    
    
    # Step 2: Initialize embedding handler
    embedder = PaperVectorStore()

    # Step 3: Store embeddings + metadata
    embedder.store_papers(papers)

    print("[INFO] All papers stored in Postgres + VectorDB.")
    
    # Step 4: Generate recommendations
    recommendations: List[Dict] = get_paper_recommendations(user_id, papers)

    print("\n[RECOMMENDATIONS]")
    for rec in recommendations:
        print(f"- {rec['title']} ({rec['pdf_url']})")
        
        
    # Step 5: Simulate user interactions
    for i, paper in enumerate(papers):
        if i == 0:
            handle_paper_interaction(user_id, paper["id"], "LIKE")  # first one liked
        else:
            handle_paper_interaction(user_id, paper["id"], "DISLIKE")  # rest disliked

    print(f"[INFO] User {user_id} interactions stored.")


if __name__ == "__main__":
    main(user_id="1")
