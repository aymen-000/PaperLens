from sqlalchemy import Column, Integer, ForeignKey, ARRAY, String, Date, Time
from sqlalchemy.orm import relationship
from backend.app.database import Base

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topics = Column(ARRAY(String))
    categories = Column(ARRAY(String))
    max_results = Column(Integer, default=10)
    notification_channel = Column(String, default="email")  # email | telegram | slack
    notification_time = Column(Time, nullable=True)


    user = relationship("User", back_populates="preferences")
