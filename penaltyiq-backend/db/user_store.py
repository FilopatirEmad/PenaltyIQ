"""
User Store — PenaltyIQ Backend
================================
SQLite-backed user CRUD. Uses Python's built-in sqlite3 module —
no ORM, no external dependencies.

Database is auto-created at DB_PATH on first use.
All operations use parameterised queries to prevent SQL injection.
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from passlib.context import CryptContext

logger = logging.getLogger("penaltyiq.user_store")

DB_PATH: str = os.getenv("DB_PATH", "./penaltyiq.db")
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class User:
    id: int
    name: str
    email: str
    hashed_password: str
    role: str          # "user" | "admin"


# ── DB Initialisation ─────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")   # better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """
    Create the users table if it does not exist.
    Called once at application startup.
    """
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                email           TEXT    NOT NULL UNIQUE,
                hashed_password TEXT    NOT NULL,
                role            TEXT    NOT NULL DEFAULT 'user',
                created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    logger.info(f"User DB initialised at: {DB_PATH}")


# ── Password Helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_user(name: str, email: str, password: str, role: str = "user") -> User:
    """
    Create a new user. Raises ValueError if email already registered.
    """
    hashed = hash_password(password)
    try:
        with _get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, hashed_password, role) VALUES (?,?,?,?)",
                (name, email.lower(), hashed, role)
            )
            conn.commit()
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Email '{email}' is already registered.")
    return User(id=user_id, name=name, email=email.lower(),
                hashed_password=hashed, role=role)


def get_user_by_email(email: str) -> Optional[User]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
    if row is None:
        return None
    return User(
        id=row["id"], name=row["name"], email=row["email"],
        hashed_password=row["hashed_password"], role=row["role"]
    )


def get_user_by_id(user_id: int) -> Optional[User]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return User(
        id=row["id"], name=row["name"], email=row["email"],
        hashed_password=row["hashed_password"], role=row["role"]
    )


def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Return the User if credentials are valid, else None.
    Constant-time comparison prevents timing attacks via passlib.
    """
    user = get_user_by_email(email)
    if user is None:
        _pwd_context.dummy_verify()  # prevent timing oracle
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
