from flask import Flask, request, jsonify
from typing import List, Dict
import uuid
import numpy as np
import os
from werkzeug.exceptions import BadRequest
from datetime import date
# Import your modules
from agents.system_agents.crawler import run_agent
from agents.data.embedding import handle_paper_interaction, get_paper_recommendations, MultimodalEmbedder
from agents.data.vector_db import PaperVectorStore
from agents.data.indexing import FAISSIndex
from agents.lib.chunker import TextChunker
from backend.app.services.preprocessing import PaperPreprocessor
from werkzeug.utils import secure_filename
import os
import requests
from flask import Flask, request, jsonify
from backend.app.services.db_service import insert_paper , get_db
app = Flask(__name__)

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
# Check api 
# ======================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Paper Research API is running"})



# ======================
# Crawle agent
# ======================


@app.route('/crawl-papers', methods=['POST'])
def crawl_papers():
    """Crawl papers for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        thread_id = data.get('thread_id', str(uuid.uuid4()))
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        papers = run_agent(user_id=user_id, thread_id=thread_id)
        
        return jsonify({
            "success": True,
            "thread_id": thread_id,
            "papers_count": len(papers),
            "papers": papers,
            "message": f"Successfully crawled {len(papers)} papers"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# Store papers endpoint (just embedding)  + put in database 
# =========================================================

@app.route('/store-papers', methods=['POST'])
def store_papers():
    """Store papers in vector database"""
    try:
        data = request.get_json()
        papers = data.get('papers', [])
        user_id = data.get("user_id" , "")
        
        if not papers:
            return jsonify({"error": "papers array is required"}), 400
        
        paper_store = PaperVectorStore()
        paper_store.store_papers(papers)
        with get_db() as db:
            for paper in papers: 
                insert_paper(
                    db,
                    id=paper["id"] , 
                    user_id= user_id  ,
                    title= paper["title"],
                    abstract=paper["summary"],
                    authors=paper["authors"],
                    categories=paper["categories"],
                    source_url=paper["pdf_url"] , 
                    published_at=date.today()
                )

        return jsonify({
            "success": True,
            "stored_count": len(papers),
            "message": "Papers stored successfully in Postgres + VectorDB"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
# ======================
# Papers Downloader API 
# ======================
import arxiv 
import re

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
        print(f"Error: Paper with ID '{arxiv_id}' not found on arXiv.")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

@app.route("/process_paper", methods=["POST"])
def process_paper():
    try:
        data = request.json
        arxiv_id = data.get("id")  # Changed variable name for clarity
        
        if not arxiv_id:
            return jsonify({"error": "No arxiv ID provided"}), 400
        
        # Step 1: Download PDF
        papers_dir = "./storage/papers/"
        os.makedirs(papers_dir, exist_ok=True)  # Ensure directory exists
        
        paper_title, pdf_path = download_arxiv_paper_by_id(arxiv_id, download_dir=papers_dir)
        
        if not paper_title:  # Check if download failed
            return jsonify({"error": "Failed to download paper"}), 500
        
        # Step 2: Process PDF
        processed_dir = "./storage/processed/paper_"+ paper_title
        os.makedirs(processed_dir, exist_ok=True)
        
        processor = PaperPreprocessor(pdf_path, output_dir=processed_dir)
        result = processor.process()
        
        return jsonify({
            "message": "Paper processed successfully",
            "paper_title": paper_title,
            "raw_pdf_path": pdf_path,
            "processed_dir": processed_dir,
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
    
    

if __name__ == "__main__":
    app.run(debug=True, port=5000)  
    
    

    
    