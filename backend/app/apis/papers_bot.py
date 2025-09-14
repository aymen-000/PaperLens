from flask import Flask, request, jsonify
from typing import List, Dict
import uuid
import numpy as np
import os
from werkzeug.exceptions import BadRequest

# Import your modules
from agents.system_agents.crawler import run_agent
from agents.data.embedding import handle_paper_interaction, get_paper_recommendations, MultimodalEmbedder
from agents.data.vector_db import PaperVectorStore
from agents.data.indexing import FAISSIndex
from agents.lib.chunker import TextChunker
from agents.system_agents.papers_rag import run_paper_rag
from backend.app.services.db_service import get_db , insert_chat_history
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

# ====================
# Papers bot endpoint
# ====================

@app.route("/paper_chat" , methods=["POST"]) 
def paper_chat() : 
    """ Chat bot for papers """
    try : 
        data = request.get_json()
        query = data.get("query" , "")
        paper_id = data.get("paper_id", "")
        user_id = data.get("user_id" , "")
        thread_id = data.get("thread_id" , "")
        
        response = run_paper_rag(query=query , paper_id=paper_id , user_id=user_id , thread_id=thread_id)
        # response["answer"] => should be stored in out db chats_history  : user_id , paper_id , content 
        with get_db() as db :    
            history = insert_chat_history(db , thread_id , response["answer"] , user_id , paper_id)
        return jsonify({
            "success": True,
            "response" : response
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        



@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=5000)