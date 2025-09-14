from sqlalchemy import Column , String , ForeignKey
from backend.app.database import Base
from sqlalchemy.orm import relationship




   
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(50), primary_key=True)
    session_id = Column(String(50))
    content = Column(String)

    # --- foreign keys ---
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(String, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    # --- relationships ---
    user = relationship("User", back_populates="chat_history")
    paper = relationship("Paper", back_populates="chat_history")