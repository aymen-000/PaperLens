from sqlalchemy import Column , Text , String , ARRAY , Date
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
    
    