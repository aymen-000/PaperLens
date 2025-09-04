from typing import List, Dict
from agents.system_agents.crawler import run_agent
from agents.data.embedding import handle_paper_interaction , get_paper_recommendations
from agents.data.vector_db import PaperVectorStore
import uuid
def main(user_id:str , thread_id:str=None):
    # Step 1: Crawl papers
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "user_id": "1",  
            "thread_id": thread_id,
        }
    }
    user_id = "1" 
    papers = run_agent(user_id=user_id , thread_id=thread_id)  
    print(f"[INFO] Crawled {len(papers)} papers.")
    
    

    embedder = PaperVectorStore()


    embedder.store_papers(papers)

    print("[INFO] All papers stored in Postgres + VectorDB.")
    

    recommendations: List[Dict] = get_paper_recommendations(user_id, papers)

    print("\n[RECOMMENDATIONS]")
    for rec in recommendations:
       print(f"- {rec['title']} ({rec['pdf_url']})")
       print(rec['relevance_score'])
        
        

    for i, paper in enumerate(papers):
        if i == 0:
            handle_paper_interaction(user_id, paper, "LIKE")  
        else:
            handle_paper_interaction(user_id, paper, "DISLIKE")  

    print(f"[INFO] User {user_id} interactions stored.")


if __name__ == "__main__":
    main(user_id="1")
