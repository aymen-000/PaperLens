import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional
from collections import defaultdict


class FAISSIndex:
    """
    Wrapper around FAISS index for text + image embeddings,
    with support for storing and retrieving by paper_id.
    Supports multiple chunks (text + images) per paper.
    """
    
    def __init__(self, dim: int, index_path: str = "faiss_index/index_rag.faiss"):
        self.dim = dim
        self.index_path = index_path
        self.metadata_path = index_path.replace('.faiss', '_metadata.json')
        self.index = faiss.IndexFlatL2(dim)
        self.metadata: List[Dict[str, Any]] = []
        # Changed: now maps paper_id to list of indices
        self.id_to_indices: Dict[str, List[int]] = defaultdict(list)

        os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    def add_embeddings(self, embeddings, metadatas: List[Dict[str, Any]]):
        """Add embeddings and their metadata (must include 'paper_id' and 'chunk_type')."""
        if not embeddings:
            return
            
        if len(embeddings) != len(metadatas):
            raise ValueError("Number of embeddings must match number of metadata entries")
            
        # Validate embedding dimensions and required fields
        for i, (emb, meta) in enumerate(zip(embeddings, metadatas)):
            if len(emb) != self.dim:
                raise ValueError(f"Embedding {i} has dimension {len(emb)}, expected {self.dim}")
            if "paper_id" not in meta:
                raise ValueError(f"Metadata {i} must include a 'paper_id'")
            if "chunk_type" not in meta:
                raise ValueError(f"Metadata {i} must include a 'chunk_type' (e.g., 'text', 'image')")
        
        np_embs = np.array(embeddings, dtype=np.float32)
        start_idx = self.index.ntotal
        self.index.add(np_embs)

        # Add to metadata and update id_to_indices mapping
        for i, meta in enumerate(metadatas):
            paper_id = meta["paper_id"]
            current_idx = start_idx + i
            
            self.metadata.append(meta)
            self.id_to_indices[paper_id].append(current_idx)
    
    def search(
        self, 
        query_emb: List[float], 
        top_k: int = 5, 
        paper_id: Optional[str] = None,
        chunk_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            query_emb: Query embedding vector
            top_k: Number of results to return
            paper_id: If provided, restrict search to this paper's chunks
            chunk_type: If provided, restrict to specific chunk type ('text', 'image', etc.)
        """
        if len(query_emb) != self.dim:
            raise ValueError(f"Query embedding has dimension {len(query_emb)}, expected {self.dim}")
        
        if self.index.ntotal == 0:
            return []
        
        np_query = np.array([query_emb], dtype=np.float32)

        if paper_id is None:
            # === Global search ===
            search_k = min(top_k * 2, self.index.ntotal)  # Get more to filter by chunk_type
            distances, indices = self.index.search(np_query, search_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.metadata):
                    meta = self.metadata[idx]
                    
                    # Filter by chunk_type if specified
                    if chunk_type and meta.get("chunk_type") != chunk_type:
                        continue
                        
                    result = meta.copy()
                    result["score"] = float(distances[0][i])
                    results.append(result)
                    
                    if len(results) >= top_k:
                        break
            return results
        
        else:
            # === Restricted search (only within one paper) ===
            if paper_id not in self.id_to_indices:
                return []
                
            candidate_indices = self.id_to_indices[paper_id]
            
            # Filter by chunk_type if specified
            if chunk_type:
                candidate_indices = [
                    idx for idx in candidate_indices 
                    if self.metadata[idx].get("chunk_type") == chunk_type
                ]
            
            if not candidate_indices:
                return []

            # Get embeddings for candidate indices
            all_embs = np.array([self.index.reconstruct(i) for i in candidate_indices], dtype=np.float32)
            query = np_query[0]

            # Compute L2 distance manually
            distances = np.linalg.norm(all_embs - query, axis=1)

            # Rank results
            top_indices = np.argsort(distances)[:min(top_k, len(distances))]
            results = []
            for j in top_indices:
                meta = self.metadata[candidate_indices[j]].copy()
                meta["score"] = float(distances[j])
                results.append(meta)
            
            return results

    def get_by_paper_id(self, paper_id: str, chunk_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a given paper_id.
        
        Args:
            paper_id: The paper ID to retrieve
            chunk_type: Optional filter by chunk type
        """
        if paper_id not in self.id_to_indices:
            return []
        
        indices = self.id_to_indices[paper_id]
        results = []
        
        for idx in indices:
            meta = self.metadata[idx].copy()
            
            # Filter by chunk_type if specified
            if chunk_type and meta.get("chunk_type") != chunk_type:
                continue
                
            meta["vector_index"] = idx
            results.append(meta)
        
        return results
    
    def get_paper_stats(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific paper."""
        if paper_id not in self.id_to_indices:
            return None
        
        indices = self.id_to_indices[paper_id]
        chunk_types = {}
        
        for idx in indices:
            chunk_type = self.metadata[idx].get("chunk_type", "unknown")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "paper_id": paper_id,
            "total_chunks": len(indices),
            "chunk_types": chunk_types,
            "indices": indices
        }
    
    def save(self):
        """Save both the FAISS index and metadata + id_to_indices."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": self.metadata,
                "id_to_indices": dict(self.id_to_indices)  # Convert defaultdict to dict
            }, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """Load both the FAISS index and metadata + id_to_indices."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        
        self.index = faiss.read_index(self.index_path)
        
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data.get("metadata", [])
                # Convert back to defaultdict
                id_to_indices = data.get("id_to_indices", {})
                self.id_to_indices = defaultdict(list, id_to_indices)
        else:
            self.metadata = [{}] * self.index.ntotal
            self.id_to_indices = defaultdict(list)
            print(f"Warning: No metadata file found at {self.metadata_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        # Count chunk types
        chunk_types = {}
        for meta in self.metadata:
            chunk_type = meta.get("type", "unknown")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dim,
            "metadata_entries": len(self.metadata),
            "unique_papers": len(self.id_to_indices),
            "chunk_types": chunk_types,
            "index_path": self.index_path,
            "metadata_path": self.metadata_path
        }
    
    def clear(self):
        """Clear the index, metadata, and id mapping."""
        self.index = faiss.IndexFlatL2(self.dim)
        self.metadata = []
        self.id_to_indices = defaultdict(list)