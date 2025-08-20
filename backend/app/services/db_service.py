from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os 
from dotenv import load_dotenv
from backend.app.models.user_preferences import UserPreferences
from backend.app.models.paper import Paper
from backend.app.models.user_embedding import UserEmbedding
from contextlib import contextmanager
import numpy as np 
load_dotenv()
database_url = os.environ.get("DATABASE_URL")
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- SESSION HANDLER ---
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
        
# --- USER PREFERENCES ---
def get_user_preferences(db, user_id:str):
    """Fetch user preferences from DB."""
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()


# --- PAPERS ---
def paper_exists(db, title:str):
    """Check if paper already exists."""
    return db.query(Paper).filter(
        Paper.title == title,
    ).first() is not None
    
    
def insert_paper(db, title:str, abstract:str, authors:list, categories:list, published_at, source_url:str):
    """Insert a new paper and return it."""
    paper = Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        categories=categories,
        published=published_at,
        url=source_url,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


def get_embedding(db, user_id: str):
    """Return UserEmbedding row for the given user_id."""
    return db.query(UserEmbedding).filter(UserEmbedding.user_id == user_id).first()

def update_user_embedding(db , user_id: str, new_paper_embedding: np.ndarray):
    """
    Blend old embedding with new paper embedding.
    """
    row = get_embedding(db, user_id=user_id)
    row.embedding = new_paper_embedding.tolist()

    db.commit()

    
    
    


    
    