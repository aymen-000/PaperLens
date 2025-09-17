from flask import Blueprint, request, jsonify
from typing import List, Dict
import uuid
import numpy as np
import os
import re
from werkzeug.exceptions import BadRequest
from datetime import date
from werkzeug.utils import secure_filename

from agents.system_agents.crawler import run_agent
from agents.data.embedding import handle_paper_interaction, get_paper_recommendations, MultimodalEmbedder
from agents.data.vector_db import PaperVectorStore
from agents.data.indexing import FAISSIndex
from agents.lib.chunker import TextChunker
from backend.app.services.preprocessing import PaperPreprocessor
from backend.app.services.db_service import insert_paper, get_db , update_paper_like
import requests
import arxiv 
from backend.app.models.paper import Paper
# Create Blueprint
paper_bp = Blueprint("paper_api", __name__, url_prefix="/api/papers")

# Initialize components
embedder_instance = None
text_chunker = TextChunker(chunk_size=400, overlap=10)

def get_embedder():
    """Get or create embedder instance"""
    global embedder_instance
    if embedder_instance is None:
        embedder_instance = MultimodalEmbedder()
    return embedder_instance

# ======================
# Health Check
# ======================
@paper_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Paper Research API is running"})



# ======================
# Paper Downloader
# ======================
def download_arxiv_paper_by_id(arxiv_id, download_dir="./"):
    try:
        search_results = arxiv.Search(id_list=[arxiv_id]).results()
        paper = next(search_results)
        
        # Sanitize filename - remove invalid characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', paper.title)
        safe_title = safe_title.strip()[:100]  # Limit length
        
        paper.download_pdf(dirpath=download_dir, filename=f"{safe_title}.pdf")
        
        full_path = os.path.join(download_dir, f"{safe_title}.pdf")
        print(f"Successfully downloaded '{paper.title}' to {full_path}")
        return paper.title, full_path
        
    except StopIteration:
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def process_paper(arxiv_id):
    try:

        
        if not arxiv_id:
            return jsonify({"error": "No arxiv ID provided"}), 400
        
        # Step 1: Download PDF
        papers_dir = "./storage/papers/"
        os.makedirs(papers_dir, exist_ok=True)
        
        paper_title, pdf_path = download_arxiv_paper_by_id(arxiv_id, download_dir=papers_dir)
        
        if not paper_title:
            return jsonify({"error": "Failed to download paper"}), 500
        
        # Step 2: Process PDF
        processed_dir = "./storage/processed/paper_" + paper_title
        os.makedirs(processed_dir, exist_ok=True)
        
        processor = PaperPreprocessor(pdf_path, output_dir=processed_dir)
        result = processor.process()
        
        return result
        
    except Exception as e:
        print(f"error in processing paper {e}")
        return None
    
# ======================
# Crawl agent
# ======================
@paper_bp.route('/crawl-papers', methods=['POST'])
def crawl_papers():
    """Crawl papers for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        thread_id = data.get('thread_id', str(uuid.uuid4()))
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        papers = run_agent(user_id=user_id, thread_id=thread_id)
        if not papers:
            return jsonify({"error": "papers array is required"}), 400
        
        paper_store = PaperVectorStore()
        paper_store.store_papers(papers) 
        with get_db() as db:
            for paper in papers: 
                url = paper["id"]
                arxiv_id = url.split("/")[-1]
                results = process_paper(arxiv_id)
                if results : 
                    insert_paper(
                        db,
                        id=paper["id"], 
                        user_id=user_id,
                        title=paper["title"],
                        abstract=paper["summary"],
                        authors=paper["authors"],
                        categories=paper["categories"],
                        source_url=paper["pdf_url"], 
                        published_at=date.today()
                    )
                
        
        return jsonify({
            "success": True,
            "thread_id": thread_id,
            "papers_count": len(papers),
            "papers": papers,
            "message": f"Successfully crawled {len(papers)} papers"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======================
# Store papers endpoint
# ======================
@paper_bp.route('/store-papers', methods=['POST'])
def store_papers():
    """Store papers in vector database"""
    try:
        data = request.get_json()
        papers = data.get('papers', [])
        user_id = data.get("user_id", "")
        
        if not papers:
            return jsonify({"error": "papers array is required"}), 400
        
        paper_store = PaperVectorStore()
        paper_store.store_papers(papers)
        with get_db() as db:
            for paper in papers: 
                results = process_paper(paper["id"])
                insert_paper(
                    db,
                    id=paper["id"], 
                    user_id=user_id,
                    title=paper["title"],
                    abstract=paper["summary"],
                    authors=paper["authors"],
                    categories=paper["categories"],
                    source_url=paper["pdf_url"], 
                    published_at=date.today()
                )

        return jsonify({
            "success": True,
            "stored_count": len(papers),
            "message": "Papers stored successfully in Postgres + VectorDB"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================
# Load papers from our db 
# ==========================
@paper_bp.route('/load_papers', methods=['GET'])
def get_all_papers():
    """Fetch all papers for a user from the database"""
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        with get_db() as db:
            papers = (
                db.query(Paper)
                .filter(Paper.user_id == user_id)
                .order_by(Paper.published.desc())
                .all()
            )

            papers_list = [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "title": p.title,
                    "abstract": p.abstract,
                    "authors": p.authors,        # already ARRAY
                    "categories": p.categories,  # already ARRAY
                    "url": p.url,
                    "published": p.published.isoformat() if p.published else None , 
                    "like": p.like
                }
                for p in papers
            ]

            return jsonify({"success": True, "count": len(papers_list), "papers": papers_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# ===================
# Like papeer endpoint 
# ===================
@paper_bp.route("/like_paper", methods=["POST"])
def like_paper():
    data = request.get_json()

    paper_id = data.get("paper_id")
    user_id = data.get("user_id")
    like = data.get("like")

    if paper_id is None or user_id is None or like is None:
        return jsonify({"error": "Missing paper_id, user_id, or like"}), 400

    with get_db() as db : 

        paper = update_paper_like(db, paper_id, user_id, like)

    if not paper:
        return jsonify({"error": f"No paper found with id={paper_id} for user_id={user_id}"}), 404

    return jsonify({
        "message": "Paper updated successfully",
        "paper_id": paper.id,
        "like": paper.like
    })