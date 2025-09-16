from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS   # 👈 add this
from backend.app.services.db_service import get_db , insert_paper 
from datetime import date 
from agents.system_agents.crawler import run_agent
from agents.data.vector_db import PaperVectorStore

from backend.app.services.db_service import insert_paper, get_db
from backend.app.models.paper import Paper
import uuid 
from backend.app.models.user import User
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime
def crawl_and_store():
    with get_db() as db:
        users = db.query(User).all()
        paper_store = PaperVectorStore()

        for user in users:
            papers = run_agent(user_id=user.id, thread_id=str(uuid.uuid4()))
            if not papers:
                continue

            paper_store.store_papers(papers)
            
            # similarity search with user profile 
            for paper in papers:
                insert_paper(
                    db,
                    id=paper["id"],
                    user_id=user.id,
                    title=paper["title"],
                    abstract=paper["summary"],
                    authors=paper["authors"],
                    categories=paper["categories"],
                    source_url=paper["pdf_url"],
                    published_at=date.today(),
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
    scheduler.add_job(func=crawl_and_store, trigger="interval", days=1)
    scheduler.start()
    

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
