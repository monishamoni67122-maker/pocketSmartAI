"""
Simple in-memory auth service for PocketSmart AI.
For production replace with a real database.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict

from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "pocket-smart-dev-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory user store  {username: user_dict}
_users: Dict[str, dict] = {}
# Simple history store  {user_id: [recommendations]}
_history: Dict[str, list] = {}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_user(username: str, email: str, password: str, full_name: Optional[str] = None) -> dict:
    if username in _users:
        raise ValueError("Username already registered")
    for u in _users.values():
        if u["email"] == email:
            raise ValueError("Email already registered")
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name or username,
        "hashed_password": hash_password(password),
        "created_at": datetime.utcnow().isoformat(),
    }
    _users[username] = user
    _history[user_id] = []
    return {k: v for k, v in user.items() if k != "hashed_password"}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = _users.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return {k: v for k, v in user.items() if k != "hashed_password"}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_by_username(username: str) -> Optional[dict]:
    user = _users.get(username)
    if user:
        return {k: v for k, v in user.items() if k != "hashed_password"}
    return None


def add_to_history(user_id: str, entry: dict):
    if user_id not in _history:
        _history[user_id] = []
    entry["id"] = str(uuid.uuid4())
    entry["saved_at"] = datetime.utcnow().isoformat() + "Z"
    _history[user_id].insert(0, entry)
    # keep last 50
    _history[user_id] = _history[user_id][:50]


def get_history(user_id: str) -> list:
    return _history.get(user_id, [])


# Seed a demo user for convenience
def seed_demo_user():
    if "demo" not in _users:
        create_user("demo", "demo@pocketsmart.ai", "demo123", "Demo User")


seed_demo_user()
