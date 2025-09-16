from flask import Blueprint, request, jsonify
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
from backend.app.services.db_service import get_db, insert_chat_history

# Create Blueprint
papers_bot_bp = Blueprint("papers_bot", __name__, url_prefix="/api/bot")

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
@papers_bot_bp.route("/paper_chat", methods=["POST"])
def paper_chat():
    """Chat bot for papers"""
    try:
        data = request.get_json()
        query = data.get("query", "")
        paper_id = data.get("paper_id", "")
        user_id = data.get("user_id", "")
        thread_id = data.get("thread_id", "")

        response = run_paper_rag(
            query=query,
            paper_id=paper_id,
            user_id=user_id,
            thread_id=thread_id
        )

        # Store in chat history
        with get_db() as db:
            insert_chat_history(db, thread_id, response["answer"], user_id, paper_id)

        return jsonify({
            "success": True,
            "response": response
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ==========================
# Load chat history
# ==========================

@papers_bot_bp.route("/chat-history", methods=["GET"])
def get_chat_history():
    """Fetch chat history with optional filters (user_id, paper_id, session_id)"""
    try:
        user_id = request.args.get("user_id")
        paper_id = request.args.get("paper_id")

        query = """
            SELECT id, session_id, content, user_id, paper_id
            FROM chat_history
            WHERE 1=1
        """
        params = []

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        if paper_id:
            query += " AND paper_id = %s"
            params.append(paper_id)

        query += " ORDER BY id ASC"

        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            cursor.close()

            history = [
                {
                    "id": row[0],
                    "session_id": row[1],
                    "content": row[2],
                    "user_id": row[3],
                    "paper_id": row[4]
                }
                for row in rows
            ]

            return jsonify({"success": True, "count": len(history), "history": history})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================
# Error handlers
# ====================
@papers_bot_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@papers_bot_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
