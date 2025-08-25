from sqlalchemy import Column, Integer, ForeignKey, String, Float, Time
from sqlalchemy.orm import relationship
from backend.app.database import Base

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    notification_channel = Column(String, default="email")  # email | telegram | slack
    notification_time = Column(Time, nullable=True)

    user = relationship("User", back_populates="preferences")
    categories = relationship("UserCategoryPreference", cascade="all, delete-orphan")

class UserCategoryPreference(Base):
    __tablename__ = "user_category_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_preferences.user_id", ondelete="CASCADE"))
    category = Column(String, nullable=False)
    weight = Column(Float, default=0.0)
