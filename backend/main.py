import hashlib
import json
import logging
import os
from pathlib import Path
import secrets
import time

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuthSession, SecurityLevel, User
from backend.schemas import DeleteAccountRequest, LoginRequest, RegisterRequest
from backend.security import hash_password, password_hasher, verify_password

app = FastAPI(title="MusicAccess API", version="1.0.0")
logger = logging.getLogger("musicaccess")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
COOKIE = "musicaccess_session"
SECURE_COOKIE = os.getenv("APP_ENV", "development") == "production"
SESSION_SECONDS = 60 * 60 * 12
DUMMY_HASH = hash_password("Unknown-account-123!")


def log(event: str, level=logging.INFO, **fields):
    logger.log(level, json.dumps({"level": logging.getLevelName(level), "event": event, **fields}))


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # No CORS: the frontend and API share an origin through the proxy.
    # This custom header cannot be sent by cross-origin forms or simple fetches.
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("X-MusicAccess") != "1" or request.headers.get("Sec-Fetch-Site") == "cross-site":
            log("csrf_denied", status=403)
            return JSONResponse({"detail": "Запрос отклонён защитой CSRF"}, status_code=403,
                                headers={"Cache-Control": "no-store"})
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


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_session(request: Request, db: Session = Depends(get_db)) -> AuthSession:
    token = request.cookies.get(COOKIE)
    session = db.get(AuthSession, digest(token)) if token else None
    if session is None or session.expires_at <= int(time.time()):
        log("authentication_required", status=401)
        raise HTTPException(401, "Войдите в аккаунт")
    return session


def current_user(session: AuthSession = Depends(current_session), db: Session = Depends(get_db)) -> User:
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "Войдите в аккаунт")
    return user


def csrf(request: Request, session: AuthSession = Depends(current_session)):
    if not secrets.compare_digest(request.headers.get("X-CSRF-Token", ""), session.csrf_token):
        log("csrf_denied", status=403)
        raise HTTPException(403, "Недействительный CSRF-токен. Обновите страницу")


def user_data(user: User):
    return {"id": user.id, "login": user.login, "email": user.email,
            "is_music_account": user.is_music_account, "clearance_level": user.clearance_level}


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
                is_music_account=payload.is_music_account, clearance_level=SecurityLevel.PUBLIC)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        log("registration_conflict", status=409)
        raise HTTPException(409, "Этот логин уже занят") from None
    log("registration_success", user_id=user.id)
    return {"message": "Регистрация успешна! Теперь войдите в аккаунт", "user": user_data(user)}


@app.post("/api/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login == payload.login.lower()))
    valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if not valid or user is None:
        log("login_failed", status=401)
        raise HTTPException(401, "Неверный логин или пароль")
    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
    old_token = request.cookies.get(COOKIE)
    if old_token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == digest(old_token)))
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= int(time.time())))
    token = secrets.token_urlsafe(32)
    session = AuthSession(token_hash=digest(token), user_id=user.id,
                          csrf_token=secrets.token_urlsafe(32), expires_at=int(time.time()) + SESSION_SECONDS)
    db.add(session)
    db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=SECURE_COOKIE, samesite="lax", path="/")
    log("login_success", user_id=user.id)
    return {"user": user_data(user), "csrf_token": session.csrf_token}


@app.get("/api/me")
def me(user: User = Depends(current_user), session: AuthSession = Depends(current_session)):
    return {"user": user_data(user), "csrf_token": session.csrf_token}


@app.post("/api/logout", status_code=204, dependencies=[Depends(csrf)])
def logout(response: Response, session: AuthSession = Depends(current_session), db: Session = Depends(get_db)):
    db.delete(session)
    db.commit()
    response.delete_cookie(COOKIE, path="/", httponly=True, secure=SECURE_COOKIE, samesite="lax")
    log("logout_success")


@app.delete("/api/me", status_code=204, dependencies=[Depends(csrf)])
def delete_account(payload: DeleteAccountRequest, response: Response,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(400, "Неверный пароль")
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE, path="/", httponly=True, secure=SECURE_COOKIE, samesite="lax")
    log("account_deleted", user_id=user.id)
