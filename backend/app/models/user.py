from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    password = Column(String(250), nullable=False)
    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    embedding = relationship("UserEmbedding", back_populates="user", uselist=False)
    feedback = relationship("UserFeedback", back_populates="user")
    papers = relationship("Paper" , back_populates="user")
    chat_history = relationship("ChatHistory" , back_populates="user")