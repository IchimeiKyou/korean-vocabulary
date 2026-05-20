import json
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    avatar_emoji: Optional[str] = "🧑‍🎓"


class UserLogin(BaseModel):
    username: str
    password: str


class ProgressSync(BaseModel):
    study_seconds: int
    study_date: str
    learned_ids: list[int] = []
    mastered_ids: list[int] = []


class UserResponse(BaseModel):
    id: int
    username: str
    location: str
    avatar_emoji: str
    total_study_seconds: int
    words_mastered: int
    words_learned: int
    streak_days: int
    last_study_date: str
    learned_ids: list[int] = []
    mastered_ids: list[int] = []
    created_at: datetime
    updated_at: datetime

    @field_validator('learned_ids', 'mastered_ids', mode='before')
    @classmethod
    def parse_ids(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    location: str
    avatar_emoji: str
    total_study_seconds: int
    words_mastered: int
    words_learned: int
    streak_days: int
