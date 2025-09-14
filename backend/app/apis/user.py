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

app = Flask(__name__)


# =====================
# Get paper recomondation enedpoint 
# =====================
@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get paper recommendations for a user"""
    try:
        data = request.get_json()
        papers = data.get('papers', [])
        user_id = data.get("user_id" , "")
        
        if not papers:
            return jsonify({"error": "papers array is required"}), 400
        
        recommendations = get_paper_recommendations(user_id, papers)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===========================
# Interact with paper endpoint 
# ===========================

@app.route('/paper-interaction', methods=['POST'])
def paper_interaction():
    """Handle user interaction with papers (LIKE/DISLIKE)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        paper = data.get('paper')
        interaction = data.get('interaction')  # "LIKE" or "DISLIKE"
        
        if not all([user_id, paper, interaction]):
            return jsonify({"error": "user_id, paper, and interaction are required"}), 400
        
        if interaction not in ["LIKE", "DISLIKE"]:
            return jsonify({"error": "interaction must be 'LIKE' or 'DISLIKE'"}), 400
        
        handle_paper_interaction(user_id, paper, interaction)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "interaction": interaction,
            "message": f"Interaction '{interaction}' recorded successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)  