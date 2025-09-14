from sqlalchemy import Column, Text, String, ARRAY, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String(50), primary_key=True)  # arXiv ID
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    authors = Column(ARRAY(String))
    categories = Column(ARRAY(String))
    published = Column(Date, nullable=False)
    url = Column(String, nullable=False)

    # --- foreign key to users table ---
    user_id = Column(String, ForeignKey("users.id" ,  ondelete="CASCADE"), nullable=False)

    # optional: relationship to access the user directly
    user = relationship("User", back_populates="papers")
    
    chat_history = relationship("ChatHistory" , back_populates="papers")