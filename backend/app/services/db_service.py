from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os 
from dotenv import load_dotenv
from backend.app.models.user_preferences import UserCategoryPreference , UserPreferences
from backend.app.models.paper import Paper
from backend.app.models.user_embedding import UserEmbedding
from contextlib import contextmanager
import numpy as np 
from sqlalchemy.orm import Session 
from backend.app.models.chat_history import ChatHistory
import uuid
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
def get_user_preferences(db, user_id: str):
    """Fetch user preferences from DB."""
    user_pref = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not user_pref:
        user_pref = UserPreferences(user_id=user_id)
        db.add(user_pref)
        db.flush()

    # Return all category preferences for this user
    return db.query(UserCategoryPreference).filter(UserCategoryPreference.user_id == user_id).all()


# --- PAPERS ---
def paper_exists(db, title:str):
    """Check if paper already exists."""
    return db.query(Paper).filter(
        Paper.title == title,
    ).first() is not None
    
    
def insert_paper(db, id:str ,user_id : str ,  title:str, abstract:str, authors:list, categories:list, published_at, source_url:str ):
    """Insert a new paper and return it."""
    paper = Paper(
        id=id , 
        title=title,
        abstract=abstract,
        authors=authors,
        categories=categories,
        published=published_at,
        url=source_url,
        user_id=user_id
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

    
    
    
def update_user_preferences(db: Session, user_id: int, category_updates: dict[str, float]):
    """
    Update user preferences (category weights) in the database.
    Args:
        db (Session): SQLAlchemy session.
        user_id (int): User ID.
        category_updates (dict[str, float]): Category -> weight delta, e.g. {"cs.CV": 1.0, "cs.AI": -0.5}.
    """
    # Ensure user preferences exist
    user_pref = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not user_pref:
        user_pref = UserPreferences(user_id=user_id)
        db.add(user_pref)
        db.flush()  # Flush to get the ID for foreign key relationships
    
    # Fetch current categories - refresh the relationship after flush
    db.refresh(user_pref)
    existing_prefs = {
        c.category: c for c in user_pref.categories
    }
    
    # Apply updates
    for category, delta in category_updates.items():
        if category in existing_prefs:
            existing_prefs[category].weight += delta
        else:
            # Only create new categories if delta is positive
            if delta > 0:
                new_cat = UserCategoryPreference(
                    user_id=user_id,  # Keep user_id as requested
                    category=category, 
                    weight=delta
                )
                db.add(new_cat)
    
    # Flush to ensure new categories are in the database
    db.flush()
    
    # Refresh to get updated categories list
    db.refresh(user_pref)
    
    # Remove categories with weight <= 0
    categories_to_remove = [cat for cat in user_pref.categories if cat.weight <= 0]
    for cat in categories_to_remove:
        db.delete(cat)
    
    # Flush deletions
    if categories_to_remove:
        db.flush()
        db.refresh(user_pref)
    
    # Enforce max 30 categories by keeping top 30
    sorted_cats = sorted(user_pref.categories, key=lambda c: c.weight, reverse=True)
    if len(sorted_cats) > 30:
        categories_to_remove = sorted_cats[30:]
        for cat in categories_to_remove:
            db.delete(cat)
        db.flush()
        db.refresh(user_pref)
    
    # Normalize weights (so they sum to 1.0)
    total_weight = sum(c.weight for c in user_pref.categories)
    if total_weight > 0:
        for cat in user_pref.categories:
            cat.weight /= total_weight
    
    # Final commit
    db.commit()
    
    return {c.category: c.weight for c in user_pref.categories}


def insert_chat_history(
    db: Session,
    session_id: str,
    content: str,
    user_id: str,
    paper_id: str
) :
    """
    Insert a new chat history record into the database.
    """
    chat_entry = ChatHistory(
        id=str(uuid.uuid4()),   # generate unique ID
        session_id=session_id,
        content=content,
        user_id=user_id,
        paper_id=paper_id
    )
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)
    return chat_entry