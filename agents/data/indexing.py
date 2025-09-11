import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional


class FAISSIndex:
    """
    Simple wrapper around FAISS index for text + image embeddings.
    """
    
    def __init__(self, dim: int, index_path: str = "faiss_index/index_rag.faiss"):
        self.dim = dim
        self.index_path = index_path
        self.metadata_path = index_path.replace('.faiss', '_metadata.json')
        self.index = faiss.IndexFlatL2(dim)
        self.metadata: List[Dict[str, Any]] = []
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    def add_embeddings(self, embeddings , metadatas: List[Dict[str, Any]]):
        """Add embeddings and their metadata to the index."""
        if not embeddings:
            return
            
        if len(embeddings) != len(metadatas):
            raise ValueError("Number of embeddings must match number of metadata entries")
            
        # Validate embedding dimensions
        for i, emb in enumerate(embeddings):
            print("============================= len" ,i ,  len(emb))
            if len(emb) != self.dim:
                raise ValueError(f"Embedding {i} has dimension {len(emb)}, expected {self.dim}")
        
        np_embs = np.array(embeddings, dtype=np.float32)
        self.index.add(np_embs)
        self.metadata.extend(metadatas)
    
    def search(self, query_emb: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings."""
        if len(query_emb) != self.dim:
            raise ValueError(f"Query embedding has dimension {len(query_emb)}, expected {self.dim}")
            
        if self.index.ntotal == 0:
            return []
            
        # Ensure we don't search for more items than available
        top_k = min(top_k, self.index.ntotal)
        
        np_query = np.array([query_emb], dtype=np.float32)
        distances, indices = self.index.search(np_query, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):  # -1 indicates no result found
                result = self.metadata[idx].copy()
                result["score"] = float(distances[0][i])
                results.append(result)
        
        return results
    
    def save(self):
        """Save both the FAISS index and metadata."""
        # Save FAISS index
        faiss.write_index(self.index, self.index_path)
        
        # Save metadata separately as JSON
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """Load both the FAISS index and metadata."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
            
        # Load FAISS index
        self.index = faiss.read_index(self.index_path)
        
        # Load metadata if it exists
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            # If no metadata file exists, create empty metadata for existing index
            self.metadata = [{}] * self.index.ntotal
            print(f"Warning: No metadata file found at {self.metadata_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dim,
            "metadata_entries": len(self.metadata),
            "index_path": self.index_path,
            "metadata_path": self.metadata_path
        }
    
    def clear(self):
        """Clear the index and metadata."""
        self.index = faiss.IndexFlatL2(self.dim)
        self.metadata = []


""" # Example usage
if __name__ == "__main__":
    # Create index
    index = FAISSIndex(dim=768, index_path="data/embeddings.faiss")
    
    # Add some example embeddings
    embeddings = [
        [0.1] * 768,  # Example embedding 1
        [0.2] * 768,  # Example embedding 2
        [0.3] * 768,  # Example embedding 3
    ]
    
    metadatas = [
        {"text": "Example text 1", "type": "text", "id": "1"},
        {"text": "Example text 2", "type": "text", "id": "2"}, 
        {"image_path": "image1.jpg", "type": "image", "id": "3"},
    ]
    
    index.add_embeddings(embeddings, metadatas)
    
    # Search
    query_emb = [0.15] * 768
    results = index.search(query_emb, top_k=2)
    
    print("Search results:")
    for result in results:
        print(f"Score: {result['score']:.4f}, Data: {result}")
    
    # Save and load
    index.save()
    
    # Create new index and load
    new_index = FAISSIndex(dim=768, index_path="data/embeddings.faiss")
    new_index.load()
    
    print("\nIndex stats:", new_index.get_stats()) """