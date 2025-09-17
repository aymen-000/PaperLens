from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS   
from backend.app.services.db_service import get_db , insert_paper 
from datetime import date 
from agents.system_agents.crawler import run_agent
from agents.data.vector_db import PaperVectorStore

from backend.app.services.db_service import insert_paper, get_db
from backend.app.models.paper import Paper
import uuid 
from backend.app.models.user import User
from backend.app.routes.papers_api import process_paper
from apscheduler.schedulers.background import BackgroundScheduler
from agents.data.indexing import FAISSIndex
from agents.lib.chunker import TextChunker
from agents.data.embedding import MultimodalEmbedder
import os
import datetime

def papers_index(text_file , images , paper_id) : 
    with open(text_file, "r", encoding="utf-8") as f:
        raw_text = f.read()
    chunker = TextChunker(chunk_size=400    , overlap=10)
    text_chunks = chunker.semantic_splitter(raw_text) 
    embedder = MultimodalEmbedder()
    text_chunks = chunker.chunk_text(raw_text) 
    text_embs = embedder.embed_text(text_chunks)
    text_meta = [{"chunk_type": "text", "chunk": i, "content": c , "paper_id": paper_id} for i, c in enumerate(text_chunks)]
    print("[Info] Done with text embedding")
    image_embs = embedder.embed_images(images)
    image_meta = [{"chunk_type": "image", "path": p , "paper_id": paper_id} for p in images]
    # Text index
    text_index = FAISSIndex(dim=len(text_embs[0]), index_path="faiss_index/text_index.faiss")
    text_index.add_embeddings(text_embs, text_meta)
    text_index.save()

    # Image index
    image_index = FAISSIndex(dim=len(image_embs[0]), index_path="faiss_index/image_index.faiss")
    image_index.add_embeddings(image_embs, image_meta)
    image_index.save()
    print("[Info] Done with images embeddings")
def crawl_and_store():
    with get_db() as db:
        users = db.query(User).all()
        paper_store = PaperVectorStore()

        for user in users:

                papers = run_agent(user_id=user.id, thread_id=str(uuid.uuid4()))
                if not papers:
                    continue

                paper_store.store_papers(papers)
                

                for paper in papers:
                    url = paper["id"]
                    arxiv_id = url.split("/")[-1]
                    results = process_paper(arxiv_id)
                    if results : 
                        papers_index(text_file=results["text_file"] ,images = results["images"], paper_id=paper["id"] )
                        insert_paper(
                                db,
                                id=paper["id"], 
                                user_id=user.id,
                                title=paper["title"],
                                abstract=paper["summary"],
                                authors=paper["authors"],
                                categories=paper["categories"],
                                source_url=paper["pdf_url"], 
                                published_at=date.today()
                            )

  
def create_app():
    app = Flask(__name__)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    jwt = JWTManager(app)
    CORS(app)

    # Register your blueprints
    from backend.app.routes.papers_api import paper_bp
    from backend.app.routes.papers_bot import papers_bot_bp
    from backend.app.routes.user import user_bp

    app.register_blueprint(paper_bp)
    app.register_blueprint(papers_bot_bp)
    app.register_blueprint(user_bp)

    # --- Scheduler ---
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=crawl_and_store, trigger="interval", days=1 , next_run_time=datetime.datetime.now())
    scheduler.start()
    

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
