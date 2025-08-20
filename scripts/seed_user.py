import random
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from  backend.app.models.user import  User
from backend.app.models.user_preferences import   UserPreferences
from backend.app.models.user_embedding import  UserEmbedding  
from backend.app.database import Base
import os
from dotenv import load_dotenv 

load_dotenv()
# --- CONFIG ---
DB_URL = os.environ.get("DATABASE_URL")
EMBEDDING_DIM = 384 

# --- DB SETUP ---
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# --- Create schema if not exists ---
Base.metadata.create_all(bind=engine)

# --- Create a user ---
new_user = User(name="Test User", email="test1@example.com")
session.add(new_user)
session.commit()  # so user.id is generated

# --- Create user preferences ---
preferences = UserPreferences(
    user_id=new_user.id,
    topics=["machine learning", "deep learning"],
    categories=["cs.LG", "stat.ML"],
    max_results=5,
    notification_channel="email"
)
session.add(preferences)

# --- Create user embedding ---
embedding_vector = np.random.rand(EMBEDDING_DIM).tolist()  # random for demo
user_embedding = UserEmbedding(
    user_id=new_user.id,
    embedding=embedding_vector , 
    model_name = "openai"
)
session.add(user_embedding)

# --- Commit all changes ---
session.commit()

print(f"User {new_user.name} created with ID {new_user.id}")
print(f"Topics: {preferences.topics}")
print(f"Categories: {preferences.categories}")
print(f"Embedding length: {len(embedding_vector)}")