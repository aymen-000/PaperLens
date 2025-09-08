from typing import List, Dict
from agents.system_agents.crawler import run_agent
from agents.data.embedding import handle_paper_interaction , get_paper_recommendations , MultimodalEmbedder
from agents.data.vector_db import PaperVectorStore
from agents.data.indexing import FAISSIndex
from agents.lib.chunker import TextChunker
import uuid
import os 
def main(user_id:str , thread_id:str=None):
    # Step 1: Crawl papers
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "user_id": "1",  
            "thread_id": thread_id,
        }
    }
    # =========
    # Test papers scrapping , intercations , saving , recomondations ...etc 
    # =========
    """     user_id = "1" 
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

        print(f"[INFO] User {user_id} interactions stored.") """
    
    # ================
    # Test RAG piplein 
    # ================
    
    # Example
    text_file = "storage/processed/Whats_Left_Concept_Grounding_text.txt"
    with open(text_file, "r", encoding="utf-8") as f:
        raw_text = f.read()
    embedder = MultimodalEmbedder()
    chunker = TextChunker(chunk_size=10, overlap=0)
    text_chunks = chunker.chunk_text(raw_text) 
    text_embs = embedder.embed_text(text_chunks)
    text_meta = [{"type": "text", "chunk": i, "content": c} for i, c in enumerate(text_chunks)]
    print("[Info] Done with text embedding")
    image_paths = [os.path.join("storage/processed/images" , file_name ) for file_name in os.listdir("storage/processed/images") ]
    image_embs = embedder.embed_images(image_paths)
    image_meta = [{"type": "image", "path": p} for p in image_paths]
    print("[Info] Done with images embeddings")
    # Store
    index = FAISSIndex(dim=len(text_embs[0]))
    index.add_embeddings(text_embs, text_meta)
    index.add_embeddings(image_embs, image_meta)

    # Save
    index.save() 

if __name__ == "__main__":
    main(user_id="1")
