# app/auth.py
from datetime import datetime, timedelta
from typing import Optional, Generator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .db import get_db
from .models_auth import User
from .schemas_auth import UserCreate, UserOut, Token
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

# hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme used only for reading Bearer token from requests (for get_current_user)
bearer_scheme = HTTPBearer()


# ---------------- helpers ----------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ---------------- routes ----------------
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register user baru.
    Body: { "username": "...", "password": "..." }
    Response: UserOut (id, username, created_at)
    """
    existing = get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")

    hashed = get_password_hash(user_in.password)
    db_user = User(username=user_in.username, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login menggunakan form-url-encoded (username + password).
    Mengembalikan access_token (JWT) dan token_type.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# ---------------- auth dependency ----------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: ambil user dari header Authorization: Bearer <token>
    (HTTPBearer memastikan ada header; kita decode JWT di sini)
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token otentikasi tidak valid",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user_id = int(sub)
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """
    Ambil data user saat ini (menggunakan Authorization: Bearer <token>).
    """
    return current_user
