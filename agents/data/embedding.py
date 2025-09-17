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
from backend.app.services.handle_interaction import interac_with_paper
import torch
from sentence_transformers import SentenceTransformer
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, AutoTokenizer, AutoModel
from typing import List, Dict
from pathlib import Path
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
                 embedding_dim: int = 384,  # Fixed: Changed from 1536 to match model
                 learning_rate: float = 0.1, 
                 decay_factor: float = 0.95, 
                 min_interaction: int = 3):
        self.embedding_dim = embedding_dim 
        self.learning_rate = learning_rate 
        self.decay_factor = decay_factor 
        self.min_interaction = min_interaction 
        self.logger = logging.getLogger(__name__)
        
    def update_user_embedding(self, db: Session, user_id: str, paper_embeddings: List[np.ndarray], interaction_types: List[InteractionType], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):  # Fixed: Changed default model
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
  
            
            
            self.logger.info(f"Updated embedding for user {user_id} with {len(paper_embeddings)} interactions")
            return new_embedding
            
        except Exception as e:
            self.logger.error(f"Error updating user embedding for user {user_id}: {str(e)}")
            raise
        
        
    def _get_user_embedding(self, db: Session, user_id: str, model_name: str) -> np.ndarray: 
        user_embedding = db.query(UserEmbedding).filter(
            UserEmbedding.user_id == user_id, 
        ).first()
        if  user_embedding and user_embedding.embedding: 
            embedding_array = np.array(user_embedding.embedding)
            # Fixed: Ensure embedding has correct dimensions
            if embedding_array.shape[0] != self.embedding_dim:
                self.logger.warning(f"Embedding dimension mismatch. Expected {self.embedding_dim}, got {embedding_array.shape[0]}")
                return np.random.normal(0, 0.01, self.embedding_dim)
            return embedding_array
        else: 
            
            return np.random.normal(0, 0.01, self.embedding_dim)
        
        
    def _calculate_weighted_embeddings(self, 
                                     paper_embeddings: List[np.ndarray],
                                     interaction_types: List[InteractionType]) -> List[np.ndarray]:
        """Apply weights to paper embeddings based on interaction types."""
        
        # Fixed: Added validation
        if len(paper_embeddings) != len(interaction_types):
            raise ValueError("Number of embeddings must match number of interaction types")
        
        weighted_embeddings = []
        for embedding, interaction in zip(paper_embeddings, interaction_types): 
            # Fixed: Validate embedding shape
            if embedding.shape[0] != self.embedding_dim:
                self.logger.error(f"Paper embedding dimension {embedding.shape[0]} doesn't match expected {self.embedding_dim}")
                continue
                
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
        
        # Fixed: Use axis=0 for proper averaging
        avg_new_embedding = np.mean(new_embeddings, axis=0)
        
        # Fixed: Validate dimensions match
        if avg_new_embedding.shape[0] != current_embedding.shape[0]:
            self.logger.error("Embedding dimension mismatch in EMA update")
            return current_embedding
        
        # Apply EMA: new_embedding = (1-α) * old + α * new
        alpha = self.learning_rate
        updated_embedding = (1 - alpha) * current_embedding + alpha * avg_new_embedding
        
        return updated_embedding
    
    
    def _apply_temporal_decay(self, db: Session, user_id: str, embedding: np.ndarray) -> np.ndarray: 
        """Apply temporal decay to reduce influence of old preferences."""
        try:
            user_embedding_record = db.query(UserEmbedding).filter(
                UserEmbedding.user_id == user_id
            ).first()
            
            if user_embedding_record and user_embedding_record.updated_at:
                now = datetime.utcnow()
                updated_at = user_embedding_record.updated_at
                
                # Remove timezone info from updated_at if it exists
                if updated_at.tzinfo is not None:
                    updated_at = updated_at.replace(tzinfo=None)
                
                days_since_update = (now - updated_at).days
                # Fixed: Ensure decay doesn't make values too small
                decay_multiplier = max(0.1, self.decay_factor ** (days_since_update / 30))  # Monthly decay with minimum threshold
                embedding = embedding * decay_multiplier
        except Exception as e:
            self.logger.error(f"Error applying temporal decay: {str(e)}")
        
        return embedding
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Normalize embedding to unit vector."""
        norm = np.linalg.norm(embedding)
        if norm > 1e-8:  # Fixed: Better threshold for zero check
            return embedding / norm
        return embedding

    def calculate_user_similarity(self, 
                                embedding1: np.ndarray, 
                                embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two user embeddings."""
        # Fixed: Added dimension validation
        if embedding1.shape != embedding2.shape:
            self.logger.error("Embedding dimensions don't match for similarity calculation")
            return 0.0
            
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        # Fixed: Better threshold for zero check
        if norm1 < 1e-8 or norm2 < 1e-8:
            return 0.0
        
        # Fixed: Clip result to valid range [-1, 1]
        similarity = dot_product / (norm1 * norm2)
        return np.clip(similarity, -1.0, 1.0)

    def get_paper_relevance_score(self, 
                                user_embedding: np.ndarray, 
                                paper_embedding: np.ndarray) -> float:
        """Calculate how relevant a paper is to a user based on embeddings."""
        # Fixed: Added validation and better scoring
        if user_embedding.shape != paper_embedding.shape:
            self.logger.error("User and paper embedding dimensions don't match")
            return 0.0
        # Calculate cosine similarity
        cosine_sim = self.calculate_user_similarity(user_embedding, paper_embedding)
        
        # Fixed: Convert similarity to relevance score (0 to 1 range)
        # Cosine similarity ranges from -1 to 1, we map it to 0 to 1
        relevance_score = (cosine_sim + 1) / 2
        
        return relevance_score



#=====================
#papers handling
#=====================


class MultimodalEmbedder:
    """
    Encodes text and images into embeddings.
    - Text: BGE (semantic text embeddings).
    - Images: CLIP.
    - Text (CLIP): optional, for cross-modal search (text <-> images).
    """

    def __init__(
        self,
        img_model_name: str = "openai/clip-vit-base-patch32",
        text_model_name: str = "BAAI/bge-small-en-v1.5"
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- Image/Text model (CLIP) ---
        self.clip_model = CLIPModel.from_pretrained(img_model_name).to(self.device)
        self.clip_processor = CLIPProcessor.from_pretrained(img_model_name)

        # --- Text model (BGE or other) ---
        self.text_tokenizer = AutoTokenizer.from_pretrained(text_model_name)
        self.text_model = AutoModel.from_pretrained(text_model_name).to(self.device)

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        """Embed text using BGE (semantic retrieval)."""
        inputs = self.text_tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            model_output = self.text_model(**inputs)
            embeddings = model_output.last_hidden_state.mean(dim=1)  # mean pooling
            embeddings = embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)

        return embeddings.cpu().numpy().tolist()

    def embed_text_using_clip(self, texts: List[str]) -> List[List[float]]:
        """Embed text using CLIP (for cross-modal text <-> image retrieval)."""
        inputs = self.clip_processor(
            text=texts,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.device)

        with torch.no_grad():
            embeddings = self.clip_model.get_text_features(**inputs)
            embeddings = embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)

        return embeddings.cpu().numpy().tolist()

    def embed_images(self, image_paths: List[str]) -> List[List[float]]:
        """Embed images using CLIP."""
        imgs = [Image.open(path).convert("RGB") for path in image_paths]
        images = [img.resize((224, 224)) for img in imgs]
        inputs = self.clip_processor(images=images, return_tensors="pt").to(self.device)

        with torch.no_grad():
            embeddings = self.clip_model.get_image_features(**inputs)
            embeddings = embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)

        return embeddings.cpu().numpy().tolist()

    def embed(self, data: List[str], use_clip_for_text: bool = False) -> List[List[float]]:
        """
        Auto-detect input type.
        - If images → embed_images.
        - If text:
            - Default: BGE (semantic).
            - If use_clip_for_text=True → CLIP text encoder.
        """
        if all(Path(d).suffix.lower() in [".png", ".jpg", ".jpeg"] for d in data):
            return self.embed_images(data)
        else:
            if use_clip_for_text:
                return self.embed_text_using_clip(data)
            return self.embed_text(data)




# ==============
# test embedding 
# ==============

""" if __name__ == "__main__":
    embedder = MultimodalEmbedder()

    # Example text embeddings
    texts = ["A diagram of a neural network", "Quantum entanglement in physics"]
    text_emb = embedder.embed_text(texts)
    print("Text embedding shape:", len(text_emb), len(text_emb[0]))

    # Example image embeddings
    image_paths = ["storage/processed/images/page1_img1.png"]
    img_emb = embedder.embed_images(image_paths)
    print("Image embedding shape:", len(img_emb), len(img_emb[0])) """

# ====================
# embedding 
# ====================
embedding_service = UserEmbeddingService(
    embedding_dim=384,  # Fixed: Match the model's output dimension
    learning_rate=0.1,
    decay_factor=0.95 
) 

def get_db_session():
    """Fixed: Proper context manager usage"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_paper_embedding(
    paper_id: str,
    index_path: str = "faiss_index/faiss_index",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> np.ndarray:
    """Fixed: Added proper error handling and type hints"""
    try:
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

        docs = vectorstore.similarity_search("", k=10000)  # Get all docs - might need optimization
        
        for doc in docs:
            if doc.metadata.get('id') == paper_id:
                # Get the embedding for this document's content
                embedding_vector = embeddings.embed_query(doc.page_content)
                return np.array(embedding_vector, dtype=np.float32)
        
        raise ValueError(f"Paper with ID {paper_id} not found in FAISS index.")
    
    except Exception as e:
        logging.error(f"Error getting paper embedding for {paper_id}: {str(e)}")
        raise

def handle_paper_interaction(user_id: str, paper: Dict[str, str], interaction_type: str):
    """Fixed: Better error handling and validation"""
    try:
        # Validate inputs
        if not user_id or not paper or not interaction_type:
            raise ValueError("Missing required parameters")
        
        paper_id = paper.get("id")
        if not paper_id:
            raise ValueError("Paper ID is required")
        

        paper_embedding = get_paper_embedding(paper_id)
        
        interaction_mapping = {
            "like": InteractionType.LIKE,
            "dislike": InteractionType.DISLIKE,
            "view": InteractionType.VIEW,
            "bookmark": InteractionType.BOOKMARK,
            "share": InteractionType.SHARE,
            "delete": InteractionType.DELETE
        }
        
        interaction_type_lower = interaction_type.lower()
        if interaction_type_lower not in interaction_mapping:
            raise ValueError(f"Invalid interaction type: {interaction_type}")
        
        interaction = interaction_mapping[interaction_type_lower]
        
        # Update paper weights in database
        updated_weights = interac_with_paper(paper, interaction_type_lower, user_id)
        if updated_weights is not None: 
            print("Database papers weights updated with success...!")
        
        # Update user embedding
        with get_db() as db:
            new_embedding = embedding_service.update_user_embedding(
                db=db,
                user_id=user_id,
                paper_embeddings=[paper_embedding],
                interaction_types=[interaction]
            )
            update_user_embedding(db , user_id=user_id , new_paper_embedding=new_embedding)
            
    except Exception as e:
        logging.error(f"Error handling paper interaction: {str(e)}")
        raise

def get_paper_recommendations(user_id: str, candidate_papers: List[Dict]) -> List[Dict]:
    """Fixed: Better error handling and validation"""
    try:
        if not user_id or not candidate_papers:
            return []
        
        with get_db() as db:
            user_embedding = embedding_service._get_user_embedding(
                db, user_id, "sentence-transformers/all-MiniLM-L6-v2" 
            )
            
            scored_papers = []
            for paper in candidate_papers:
                try:
                    if 'id' not in paper:
                        logging.warning(f"Paper missing ID: {paper}")
                        continue
                        
                    paper_embedding = get_paper_embedding(paper['id'])
                    relevance_score = embedding_service.get_paper_relevance_score(
                        user_embedding, paper_embedding
                    )
                    
                    scored_papers.append({
                        **paper,
                        'relevance_score': float(relevance_score) 
                    })
                    
                except Exception as e:
                    logging.error(f"Error scoring paper {paper.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Fixed: Sort by relevance score (descending)
            return sorted(scored_papers, key=lambda x: x['relevance_score'], reverse=True)
    
    except Exception as e:
        logging.error(f"Error getting paper recommendations for user {user_id}: {str(e)}")
        return []