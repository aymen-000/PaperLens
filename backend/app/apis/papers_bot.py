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

# Initialize components
embedder_instance = None
text_chunker = TextChunker(chunk_size=400, overlap=10)

def get_embedder():
    """Get or create embedder instance"""
    global embedder_instance
    if embedder_instance is None:
        embedder_instance = MultimodalEmbedder()
    return embedder_instance



@app.route('/embed-text', methods=['POST'])
def embed_text_content():
    """Process and embed text content"""
    try:
        data = request.get_json()
        text = data.get('text')
        chunk_size = data.get('chunk_size', 400)
        overlap = data.get('overlap', 10)
        
        if not text:
            return jsonify({"error": "text is required"}), 400
        
        # Chunk text
        chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        text_chunks = chunker.chunk_text(text)
        
        # Embed chunks
        embedder = get_embedder()
        embeddings = embedder.embed_text(text_chunks)
        
        # Create metadata
        metadata = [{"type": "text", "chunk": i, "content": c} for i, c in enumerate(text_chunks)]
        
        return jsonify({
            "success": True,
            "chunks_count": len(text_chunks),
            "embeddings_shape": [len(embeddings), len(embeddings[0]) if embeddings else 0],
            "chunks": text_chunks,
            "metadata": metadata,
            "message": "Text embedded successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/embed-images', methods=['POST'])
def embed_images():
    """Embed images from directory"""
    try:
        data = request.get_json()
        image_directory = data.get('image_directory', 'storage/processed/images')
        
        if not os.path.exists(image_directory):
            return jsonify({"error": f"Directory {image_directory} does not exist"}), 400
        
        # Get image paths
        image_paths = [
            os.path.join(image_directory, file_name) 
            for file_name in os.listdir(image_directory)
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        ]
        
        if not image_paths:
            return jsonify({"error": "No image files found in directory"}), 400
        
        # Embed images
        embedder = get_embedder()
        embeddings = embedder.embed_images(image_paths)
        
        # Create metadata
        metadata = [{"type": "image", "path": p} for p in image_paths]
        
        return jsonify({
            "success": True,
            "images_count": len(image_paths),
            "embeddings_shape": [len(embeddings), len(embeddings[0]) if embeddings else 0],
            "image_paths": image_paths,
            "metadata": metadata,
            "message": "Images embedded successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create-index', methods=['POST'])
def create_index():
    """Create and save FAISS index"""
    try:
        data = request.get_json()
        embeddings = data.get('embeddings')
        metadata = data.get('metadata')
        index_path = data.get('index_path')
        index_type = data.get('index_type', 'text')  # 'text' or 'image'
        
        if not all([embeddings, metadata, index_path]):
            return jsonify({"error": "embeddings, metadata, and index_path are required"}), 400
        
        # Convert to numpy array
        embeddings = np.array(embeddings, dtype='float32')
        
        # Create index
        index = FAISSIndex(dim=embeddings.shape[1], index_path=index_path)
        index.add_embeddings(embeddings, metadata)
        index.save()
        
        return jsonify({
            "success": True,
            "index_path": index_path,
            "index_type": index_type,
            "embeddings_count": len(embeddings),
            "dimension": embeddings.shape[1],
            "message": f"Index created and saved at {index_path}"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
def search_multimodal():
    """Search across text and image indexes"""
    try:
        data = request.get_json()
        query = data.get('query')
        text_index_path = data.get('text_index_path', 'faiss_index/text_index.faiss')
        image_index_path = data.get('image_index_path', 'faiss_index/image_index.faiss')
        top_k = data.get('top_k', 3)
        text_dim = data.get('text_dim', 384)
        image_dim = data.get('image_dim', 512)
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        embedder = get_embedder()
        
        # Load indexes
        text_index = FAISSIndex(dim=text_dim, index_path=text_index_path)
        image_index = FAISSIndex(dim=image_dim, index_path=image_index_path)
        
        try:
            text_index.load()
            image_index.load()
        except Exception as e:
            return jsonify({"error": f"Failed to load indexes: {str(e)}"}), 500
        
        # Encode query
        query_text_emb = np.array(embedder.embed_text([query]), dtype='float32')
        query_clip_emb = np.array(embedder.embed_text_using_clip([query]), dtype='float32')
        
        # Search
        text_results = text_index.search(query_text_emb[0], top_k=top_k)
        image_results = image_index.search(query_clip_emb[0], top_k=top_k)
        
        # Merge and sort results
        all_results = [{"type": "text", **r} for r in text_results] + \
                     [{"type": "image", **r} for r in image_results]
        all_results = sorted(all_results, key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            "success": True,
            "query": query,
            "text_results_count": len(text_results),
            "image_results_count": len(image_results),
            "total_results": len(all_results),
            "results": all_results[:top_k*2]  # Return top results from both types
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process-document', methods=['POST'])
def process_document():
    """Complete document processing pipeline"""
    try:
        data = request.get_json()
        text_file_path = data.get('text_file_path')
        image_directory = data.get('image_directory', 'storage/processed/images')
        chunk_size = data.get('chunk_size', 400)
        overlap = data.get('overlap', 10)
        
        if not text_file_path:
            return jsonify({"error": "text_file_path is required"}), 400
        
        if not os.path.exists(text_file_path):
            return jsonify({"error": f"File {text_file_path} does not exist"}), 400
        
        # Read text file
        with open(text_file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Process text
        chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        text_chunks = chunker.chunk_text(raw_text)
        
        embedder = get_embedder()
        text_embs = embedder.embed_text(text_chunks)
        text_meta = [{"type": "text", "chunk": i, "content": c} for i, c in enumerate(text_chunks)]
        
        # Process images if directory exists
        image_results = None
        if os.path.exists(image_directory):
            image_paths = [
                os.path.join(image_directory, file_name) 
                for file_name in os.listdir(image_directory)
                if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
            ]
            
            if image_paths:
                image_embs = embedder.embed_images(image_paths)
                image_meta = [{"type": "image", "path": p} for p in image_paths]
                image_results = {
                    "embeddings": image_embs,
                    "metadata": image_meta,
                    "count": len(image_paths)
                }
        
        return jsonify({
            "success": True,
            "text_results": {
                "chunks_count": len(text_chunks),
                "embeddings_shape": [len(text_embs), len(text_embs[0]) if text_embs else 0],
                "metadata": text_meta
            },
            "image_results": image_results,
            "message": "Document processing completed successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/full-pipeline', methods=['POST'])
def full_pipeline():
    """Complete end-to-end pipeline"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        crawl_papers = data.get('crawl_papers', False)
        thread_id = data.get('thread_id', str(uuid.uuid4()))
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        results = {"user_id": user_id, "thread_id": thread_id}
        
        # Step 1: Crawl papers (optional)
        if crawl_papers:
            papers = run_agent(user_id=user_id, thread_id=thread_id)
            results["papers"] = {
                "count": len(papers),
                "data": papers
            }
            
            # Store papers
            paper_store = PaperVectorStore()
            paper_store.store_papers(papers)
            results["storage"] = "Papers stored successfully"
            
            # Get recommendations
            recommendations = get_paper_recommendations(user_id, papers)
            results["recommendations"] = {
                "count": len(recommendations),
                "data": recommendations
            }
        
        return jsonify({
            "success": True,
            "results": results,
            "message": "Full pipeline completed successfully"
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
    # Create necessary directories
    os.makedirs('faiss_index', exist_ok=True)
    os.makedirs('storage/processed', exist_ok=True)
    os.makedirs('storage/processed/images', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)