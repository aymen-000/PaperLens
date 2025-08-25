import numpy as np 
from typing import List, Dict, Optional, Tuple 
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from enum import Enum 
import logging 
from backend.app.models.user_embedding import UserEmbedding
from backend.app.services.db_service import update_user_embedding, get_db
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
import os 
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
load_dotenv()

class InteractionType(Enum):
    LIKE = 1.0
    DISLIKE = -0.5
    VIEW = 0.1
    BOOKMARK = 0.8
    SHARE = 0.6
    DELETE = -0.9 
    
    
class UserEmbeddingService: 
    """Service for updating user embedding"""
    
    def __init__(self, 
                 embedding_dim: int = 1536, 
                 learning_rate: float = 0.1, 
                 decay_factor: float = 0.95, 
                 min_interaction: int = 3):
        self.embedding_dim = embedding_dim 
        self.learning_rate = learning_rate 
        self.decay_factor = decay_factor 
        self.min_interaction = min_interaction 
        self.logger = logging.getLogger(__name__)
        
    def update_user_embedding(self, db: Session, user_id: str, paper_embeddings: List[np.ndarray], interaction_types: List[InteractionType], model_name: str = "text-embedding-3-large"): 
        """
        Update user embedding using weighted incremental learning.
        
        Args:
            db: Database session
            user_id: User identifier
            paper_embeddings: List of paper embedding vectors
            interaction_types: List of interaction types (like, dislike, etc.)
            model_name: Embedding model used
            
        Returns:
            Updated user embedding vector
        """
        try: 
            current_embedding = self._get_user_embedding(db, user_id, model_name) 
            # Calculate weighted paper embeddings
            weighted_embeddings = self._calculate_weighted_embeddings(
                paper_embeddings, interaction_types
            ) 
            if len(weighted_embeddings) == 0:
                return current_embedding
            
            # Update embedding using exponential moving average
            new_embedding = self._exponential_moving_average_update(
                current_embedding, weighted_embeddings
            )
            new_embedding = self._apply_temporal_decay(db, user_id, new_embedding)
            # Normalize the embedding
            new_embedding = self._normalize_embedding(new_embedding) 
            update_user_embedding(db, user_id, new_embedding)
            
            self.logger.info(f"Updated embedding for user {user_id} with {len(paper_embeddings)} interactions")
            return new_embedding
            
        except Exception as e:
            self.logger.error(f"Error updating user embedding for user {user_id}: {str(e)}")
            raise
        
        
    def _get_user_embedding(self, db: Session, user_id: str, model_name: str) -> np.ndarray: 
        user_embedding = db.query(UserEmbedding).filter(
            UserEmbedding.user_id == user_id, 
        ).first()
        
        if user_embedding and user_embedding.embedding: 
            return np.array(user_embedding.embedding)
        
        else: 
            return np.random.normal(0, 0.01, self.embedding_dim)
        
        
    def _calculate_weighted_embeddings(self, 
                                     paper_embeddings: List[np.ndarray],
                                     interaction_types: List[InteractionType]) -> List[np.ndarray]:
        """Apply weights to paper embeddings based on interaction types."""
        
        weighted_embeddings = []
        for embedding, interaction in zip(paper_embeddings, interaction_types): 
            weight = interaction.value 
            weighted_embedding = embedding * weight
            weighted_embeddings.append(weighted_embedding) 
            
        return weighted_embeddings 
    
    
    
    def _exponential_moving_average_update(self, 
                                         current_embedding: np.ndarray,
                                         new_embeddings: List[np.ndarray]) -> np.ndarray:
        """Update embedding using exponential moving average.""" 
        
        if len(new_embeddings) == 0:
            return current_embedding
        
        avg_new_embedding = np.mean(new_embeddings, axis=0)
        # Apply EMA: new_embedding = (1-α) * old + α * new
        alpha = self.learning_rate
        updated_embedding = (1 - alpha) * current_embedding + alpha * avg_new_embedding
        
        return updated_embedding
    
    
    def _apply_temporal_decay(self, db: Session, user_id: str, embedding: np.ndarray) -> np.ndarray: 
        """Apply temporal decay to reduce influence of old preferences."""
        user_embedding_record = db.query(UserEmbedding).filter(
            UserEmbedding.user_id == user_id
        ).first()
        
        if user_embedding_record and user_embedding_record.updated_at:
            # Make both datetimes timezone-aware or timezone-naive
            now = datetime.utcnow()
            updated_at = user_embedding_record.updated_at
            
            # Remove timezone info from updated_at if it exists
            if updated_at.tzinfo is not None:
                updated_at = updated_at.replace(tzinfo=None)
            
            days_since_update = (now - updated_at).days
            decay_multiplier = self.decay_factor ** (days_since_update / 30)  # Monthly decay
            embedding = embedding * decay_multiplier
        
        return embedding
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Normalize embedding to unit vector."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding


    def calculate_user_similarity(self, 
                                embedding1: np.ndarray, 
                                embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two user embeddings."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def get_paper_relevance_score(self, 
                                user_embedding: np.ndarray, 
                                paper_embedding: np.ndarray) -> float:
        """Calculate how relevant a paper is to a user based on embeddings."""
        return self.calculate_user_similarity(user_embedding, paper_embedding)

# ====================
# embedding 
# ====================
embedding_service = UserEmbeddingService(
    embedding_dim=1536,
    learning_rate=0.1,
    decay_factor=0.95 
) 

def get_db_session():
    with get_db() as db:
        return db


def get_paper_embedding(
    paper_id: str,
    index_path: str = "faiss_index/faiss_index",
    model_name="sentence-transformers/all-MiniLM-L6-v2"
):
    # Load embeddings model
    embeddings = HuggingFaceEmbeddings(model_name=model_name)

    # Check if FAISS index directory exists
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index directory not found at {index_path}")
    
    # Check if the actual index file exists
    index_file = os.path.join(index_path, "index.faiss")
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"FAISS index file not found at {index_file}")

    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    # Search for documents with matching paper_id in metadata
    docs = vectorstore.similarity_search("", k=1000)  # Get all docs
    for doc in docs:
        if doc.metadata.get('id') == paper_id:
            # Get the embedding for this document's content
            embedding_vector = embeddings.embed_query(doc.page_content)
            return np.array(embedding_vector)
    
    raise ValueError(f"Paper with ID {paper_id} not found in FAISS index.")

def handle_paper_interaction(user_id: str, paper_id: str, interaction_type: str):
    # Get paper embedding from your vector store
    paper_embedding = get_paper_embedding(paper_id)
    
    # Convert interaction type
    interaction = InteractionType.LIKE if interaction_type.lower() == "like" else InteractionType.DISLIKE
    
    # Update user embedding
    with get_db() as db:
        embedding_service.update_user_embedding(
            db=db,
            user_id=user_id,
            paper_embeddings=[paper_embedding],
            interaction_types=[interaction]
        )

def get_paper_recommendations(user_id: str, candidate_papers: List[Dict]) -> List[Dict]:
    with get_db() as db:
        user_embedding = embedding_service._get_user_embedding(db, user_id, "text-embedding-3-large")
        
        scored_papers = []
        for paper in candidate_papers:
            paper_embedding = get_paper_embedding(paper['id'])
            relevance_score = embedding_service.get_paper_relevance_score(user_embedding, paper_embedding)
            
            scored_papers.append({
                **paper,
                'relevance_score': relevance_score
            })
        
        return sorted(scored_papers, key=lambda x: x['relevance_score'], reverse=True)