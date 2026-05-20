from sqlalchemy import Column, Integer, String, DateTime, Text, func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(100), nullable=False)
    location = Column(String(100), default="")
    avatar_emoji = Column(String(10), default="🧑‍🎓")
    total_study_seconds = Column(Integer, default=0)
    words_mastered = Column(Integer, default=0)
    words_learned = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_study_date = Column(String(20), default="")
    learned_ids = Column(Text, default="[]")
    mastered_ids = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
