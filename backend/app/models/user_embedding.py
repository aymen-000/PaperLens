from sqlalchemy import Column, Integer, ForeignKey, DateTime , Float , String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from backend.app.database import Base 


class UserEmbedding(Base):
    __tablename__ = "user_embedding"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(ARRAY(Float))  # we will use VectorDB in the future 
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    model_name = Column(String)
    # Relationships
    user = relationship("User", back_populates="embedding")
