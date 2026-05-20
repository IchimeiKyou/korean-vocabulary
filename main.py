from fastapi import FastAPI, Depends, HTTPException, Query, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from contextlib import asynccontextmanager
from datetime import date
import base64
import json
import httpx

from database import get_db, init_db
from models import User
from schemas import UserCreate, UserLogin, ProgressSync, UserResponse, LeaderboardEntry


def parse_basic_auth(authorization: str | None) -> tuple[str, str] | None:
    """Parse 'Basic base64(user:pass)' header, return (username, password) or None."""
    if not authorization or not authorization.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(authorization[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
        return username, password
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Korean Vocabulary API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def detect_location(request: Request) -> str:
    """Try to detect user location from IP using a free API."""
    try:
        forwarded = request.headers.get("x-forwarded-for", "")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else ""
        )
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            return ""
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                f"https://ipapi.co/{ip}/json/",
                headers={"User-Agent": "korean-vocab-app/1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                city = data.get("city", "")
                country = data.get("country_name", "")
                if city and country:
                    return f"{country} {city}"
                return country or city or ""
    except Exception:
        pass
    return ""


async def verify_user(username: str, authorization: str | None, db: AsyncSession) -> User:
    """Verify Basic auth matches the target user. Returns User or raises 401/404."""
    creds = parse_basic_auth(authorization)
    if not creds:
        raise HTTPException(status_code=401, detail="認証が必要です")
    auth_user, auth_pass = creds
    if auth_user != username:
        raise HTTPException(status_code=403, detail="他のユーザーのデータは変更できません")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    if user.password != auth_pass:
        raise HTTPException(status_code=401, detail="パスワードが正しくありません")
    return user


@app.post("/api/register", response_model=UserResponse)
async def register(user: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    if len(user.username) < 2 or len(user.username) > 50:
        raise HTTPException(status_code=400, detail="ユーザー名は2〜50文字で入力してください")
    if len(user.password) < 4:
        raise HTTPException(status_code=400, detail="パスワードは4文字以上で入力してください")

    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="このユーザー名は既に使用されています")

    location = await detect_location(request)

    try:
        db_user = User(
            username=user.username,
            password=user.password,
            location=location,
            avatar_emoji=user.avatar_emoji or "🧑‍🎓",
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="登録処理中にエラーが発生しました")


@app.post("/api/login", response_model=UserResponse)
async def login(creds: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.username == creds.username))
    except Exception:
        raise HTTPException(status_code=500, detail="データベース接続エラーが発生しました")

    user = result.scalar_one_or_none()
    if not user or user.password != creds.password:
        raise HTTPException(status_code=401, detail="ユーザー名またはパスワードが正しくありません")

    location = await detect_location(request)
    if location and location != user.location:
        user.location = location
        try:
            await db.commit()
            await db.refresh(user)
        except Exception:
            await db.rollback()

    return user


@app.get("/api/users/{username}", response_model=UserResponse)
async def get_user(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    return user


@app.post("/api/users/{username}/sync", response_model=UserResponse)
async def sync_progress(
    username: str,
    progress: ProgressSync,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    user = await verify_user(username, authorization, db)

    # Merge server IDs with client IDs (union, never shrink)
    server_learned = set(json.loads(user.learned_ids or "[]"))
    server_mastered = set(json.loads(user.mastered_ids or "[]"))
    server_learned.update(progress.learned_ids)
    server_mastered.update(progress.mastered_ids)
    # Words marked unmastered by client are removed from mastered set
    client_mastered_set = set(progress.mastered_ids)
    client_learned_set = set(progress.learned_ids)
    unmastered = client_learned_set - client_mastered_set
    server_mastered -= unmastered

    user.learned_ids = json.dumps(sorted(server_learned))
    user.mastered_ids = json.dumps(sorted(server_mastered))
    user.words_learned = len(server_learned)
    user.words_mastered = len(server_mastered)
    user.total_study_seconds += progress.study_seconds

    today_str = progress.study_date
    if user.last_study_date:
        try:
            last = date.fromisoformat(user.last_study_date)
            current = date.fromisoformat(today_str)
            diff = (current - last).days
            if diff == 1:
                user.streak_days += 1
            elif diff > 1:
                user.streak_days = 1
        except ValueError:
            user.streak_days = 1
    else:
        user.streak_days = 1

    user.last_study_date = today_str
    await db.commit()
    await db.refresh(user)
    return user


@app.get("/api/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    sort_by: str = Query("words_mastered", pattern="^(words_mastered|total_study_seconds|streak_days|words_learned)$"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    order_col = getattr(User, sort_by)
    result = await db.execute(
        select(User)
        .order_by(desc(order_col))
        .limit(limit)
    )
    users = result.scalars().all()

    return [
        LeaderboardEntry(
            rank=i + 1,
            username=u.username,
            location=u.location,
            avatar_emoji=u.avatar_emoji,
            total_study_seconds=u.total_study_seconds,
            words_mastered=u.words_mastered,
            words_learned=u.words_learned,
            streak_days=u.streak_days,
        )
        for i, u in enumerate(users)
    ]


@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
