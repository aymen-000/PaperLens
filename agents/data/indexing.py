import faiss
import numpy as np
from typing import List, Dict, Any


class FAISSIndex:
    """
    Simple wrapper around FAISS index for text + image embeddings.
    """

    def __init__(self, dim: int, index_path: str = "faiss_index/faiss_index/index_rag.faiss"):
        self.dim = dim
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(dim)
        self.metadata: List[Dict[str, Any]] = []

    def add_embeddings(self, embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        if not embeddings:
            return
        np_embs = np.array(embeddings).astype("float32")
        self.index.add(np_embs)
        self.metadata.extend(metadatas)

    def search(self, query_emb: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        np_query = np.array([query_emb]).astype("float32")
        distances, indices = self.index.search(np_query, top_k)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["score"] = float(distances[0][i])
                results.append(result)
        return results

    def save(self):
        faiss.write_index(self.index, self.index_path)

    def load(self):
        self.index = faiss.read_index(self.index_path)


# ===============
# Test indexing 
# ===============

""" if __name__ == "__main__":
    # Example usage
    dummy_embs = [[0.1, 0.2, 0.3], [0.05, 0.25, 0.4]]
    dummy_meta = [{"type": "text", "content": "transformers"}, {"type": "text", "content": "gnn"}]

    index = FAISSIndex(dim=3)
    index.add_embeddings(dummy_embs, dummy_meta)

    q = [0.1, 0.2, 0.25]
    res = index.search(q, top_k=2)
    print(res) """
