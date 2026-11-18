import json
import logging
import os
from pathlib import Path
import time
import jwt

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import SecurityLevel, Track, User
from backend.schemas import DeleteAccountRequest, LoginRequest, RegisterRequest
from backend.security import hash_password, password_hasher, verify_password
from backend.access import require_read_access

app = FastAPI(title="MusicAccess API", version="1.0.0")

logger = logging.getLogger("musicaccess")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

COOKIE = "musicaccess_session"
SECURE_COOKIE = os.getenv("APP_ENV", "development") == "production"
SESSION_SECONDS = 60 * 60 * 72     # 3 days
DUMMY_HASH = hash_password("Unknown-account-123!")
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "backend/media")).resolve()
SECRET = os.getenv("JWT_SECRET")
if not SECRET:
    raise RuntimeError("JWT_SECRET не задан")
ALGO = "HS256"


def log(event: str, level=logging.INFO, **fields):
    logger.log(level, json.dumps({"level": logging.getLevelName(level), "event": event, **fields}))


@app.middleware("http")
async def security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        # Do not log exception text: database errors can contain input values.
        log("internal_error", logging.ERROR, method=request.method)
        return JSONResponse({"detail": "Внутренняя ошибка сервера"}, status_code=500)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    log("validation_failed", status=422)
    # Pydantic's default errors include submitted values, including passwords.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()]})


def create_token(user_id: int) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + SESSION_SECONDS}
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def current_user(
    token: str | None = Cookie(default=None, alias=COOKIE),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(401, "Войдите в аккаунт")
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Сессия истекла")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Сессия недействительна")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(401, "Войдите в аккаунт")
    return user


def user_data(user: User):
    return {"id": user.id, "login": user.login, "email": user.email,
            "clearance_level": user.clearance_level}


@app.get("/")
def root():
    return {"message": "MusicAccess API работает"}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MusicAccess Backend"}


@app.post("/api/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = User(login=payload.login.lower(), password_hash=hash_password(payload.password),
                email=str(payload.email) if payload.email else None,
                clearance_level=SecurityLevel.PUBLIC)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        log("registration_conflict", status=409)
        raise HTTPException(409, "Этот логин уже занят") from None
    log("registration_success", user_id=user.id)
    return {"message": "Регистрация успешна! Войдите в аккаунт", "user": user_data(user)}


@app.post("/api/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login == payload.login.lower()))
    valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if not valid or user is None:
        log("login_failed", status=401)
        raise HTTPException(401, "Неверный логин или пароль")
    response.set_cookie(
        COOKIE, create_token(user.id), max_age=SESSION_SECONDS,
        httponly=True, secure=SECURE_COOKIE, samesite="lax", path="/",
    )
    log("login_success", user_id=user.id)
    return {"user": user_data(user)}


@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return {"user": user_data(user)}


@app.post("/api/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/", httponly=True,
                           secure=SECURE_COOKIE, samesite="lax")
    log("logout_success")


@app.delete("/api/me", status_code=204)
def delete_account(payload: DeleteAccountRequest, response: Response,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(400, "Неверный пароль")
    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE, path="/", httponly=True,
                           secure=SECURE_COOKIE, samesite="lax")
    log("account_deleted", user_id=user.id)


def track_data(track: Track):
    return {"id": track.id, "title": track.title, "artist": track.artist,
            "security_level": track.security_level, "duration": track.duration}


@app.get("/api/tracks")
@app.get("/api/tracks/search")
def tracks(q: str = Query(default="", max_length=100), title: str = Query(default="", max_length=100),
           artist: str = Query(default="", max_length=100), db: Session = Depends(get_db)):
    # Catalogue metadata is PUBLIC; audio is the protected resource.
    query = select(Track)
    if q.strip():
        query = query.where(or_(Track.title.icontains(q.strip(), autoescape=True),
                                Track.artist.icontains(q.strip(), autoescape=True)))
    if title.strip():
        query = query.where(Track.title.icontains(title.strip(), autoescape=True))
    if artist.strip():
        query = query.where(Track.artist.icontains(artist.strip(), autoescape=True))
    return [track_data(track) for track in db.scalars(query.order_by(Track.id).limit(100))]


@app.get("/api/tracks/{track_id}")
def track_detail(track_id: int, db: Session = Depends(get_db)):
    track = db.get(Track, track_id)
    if track is None:
        raise HTTPException(404, "Трек не найден")
    return track_data(track)


@app.get("/api/me/tracks")
def available_tracks(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [track_data(track) for track in db.scalars(
        select(Track).where(Track.security_level <= user.clearance_level).order_by(Track.id))]


@app.get("/api/tracks/{track_id}/stream")
def stream(track_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    track = db.get(Track, track_id)
    if track is None:
        raise HTTPException(404, "Трек не найден")
    try:
        require_read_access(user, track)
    except HTTPException:
        log("mac_denied", user_id=user.id, track_id=track.id, status=403)
        raise
    path = (MEDIA_DIR / track.file_path).resolve()
    if not path.is_relative_to(MEDIA_DIR) or not path.is_file():
        raise HTTPException(404, "Аудиофайл не найден")
    log("mac_allowed", user_id=user.id, track_id=track.id)
    # Starlette handles Range only AFTER authentication and the MAC check.
    return FileResponse(path, media_type="audio/wav")
