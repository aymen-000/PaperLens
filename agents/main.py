from typing import List, Dict
from agents.system_agents.crawler import run_agent
from agents.data.embedding import handle_paper_interaction , get_paper_recommendations , MultimodalEmbedder
from agents.data.vector_db import PaperVectorStore
from agents.data.indexing import FAISSIndex
from agents.lib.chunker import TextChunker
import uuid
import numpy as np 
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
        
    chunker = TextChunker(chunk_size=400    , overlap=10)
    text_chunks = chunker.semantic_splitter(raw_text) 
    embedder = MultimodalEmbedder()
    
    text_chunks = chunker.chunk_text(raw_text) 
    text_embs = embedder.embed_text(text_chunks)
    text_meta = [{"type": "text", "chunk": i, "content": c} for i, c in enumerate(text_chunks)]
    print("[Info] Done with text embedding")
    image_paths = [os.path.join("storage/processed/images" , file_name ) for file_name in os.listdir("storage/processed/images") ]
    image_embs = embedder.embed_images(image_paths)
    image_meta = [{"type": "image", "path": p} for p in image_paths]
    print("[Info] Done with images embeddings")
    # Store
    # Text index
    text_index = FAISSIndex(dim=len(text_embs[0]), index_path="faiss_index/text_index.faiss")
    text_index.add_embeddings(text_embs, text_meta)
    text_index.save()

    # Image index
    image_index = FAISSIndex(dim=len(image_embs[0]), index_path="faiss_index/image_index.faiss")
    image_index.add_embeddings(image_embs, image_meta)
    image_index.save()
    
    # --- Step 1: load indexes ---
    text_index = FAISSIndex(dim=384, index_path="faiss_index/text_index.faiss")
    text_index.load()

    image_index = FAISSIndex(dim=512, index_path="faiss_index/image_index.faiss")
    image_index.load()


    # --- Step 3: encode query in both spaces ---
    query = "World models and vision models"

    query_text_emb = np.array(embedder.embed_text([query])).astype("float32")
    query_clip_emb = np.array(embedder.embed_text_using_clip([query])).astype("float32")

    # --- Step 4: search ---
    text_results = text_index.search(query_text_emb[0], top_k=3)
    image_results = image_index.search(query_clip_emb[0], top_k=3)

    # --- Step 5: merge ---
    all_results = [{"type": "text", **r} for r in text_results] + \
                [{"type": "image", **r} for r in image_results]

    all_results = sorted(all_results, key=lambda x: x['score'], reverse=True)
    print(all_results)

if __name__ == "__main__":
    main(user_id="1")
