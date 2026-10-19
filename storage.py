import sqlite3
import hashlib
import hmac
import os
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("auditxai.db")
ITERATIONS = 240_000

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _hash_password(password: str, salt: bytes | None = None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return salt.hex(), digest.hex()

def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    _, candidate = _hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, hash_hex)

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Auditor',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                source_name TEXT NOT NULL,
                transaction_count INTEGER NOT NULL,
                flagged_count INTEGER NOT NULL,
                findings_json TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        row = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@auditxai.local",)).fetchone()
        if row is None:
            salt, digest = _hash_password("AuditXAI@123")
            conn.execute(
                "INSERT INTO users(name,email,salt,password_hash,role,created_at) VALUES(?,?,?,?,?,?)",
                ("Demo Auditor", "admin@auditxai.local", salt, digest, "Administrator", datetime.now().isoformat(timespec="seconds"))
            )

def register_user(name: str, email: str, password: str):
    salt, digest = _hash_password(password)
    with connect() as conn:
        conn.execute(
            "INSERT INTO users(name,email,salt,password_hash,role,created_at) VALUES(?,?,?,?,?,?)",
            (name.strip(), email.strip().lower(), salt, digest, "Auditor", datetime.now().isoformat(timespec="seconds"))
        )
        row = conn.execute("SELECT id,name,email,role FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        return dict(row)

def authenticate(email: str, password: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if row and verify_password(password, row["salt"], row["password_hash"]):
        return {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"]}
    return None

def save_analysis(user_id: int, source_name: str, results):
    findings = results[results["review_required"]].copy()
    safe_findings = findings.astype(object).where(findings.notna(), None).to_dict(orient="records")
    with connect() as conn:
        conn.execute(
            "INSERT INTO analyses(user_id,created_at,source_name,transaction_count,flagged_count,findings_json) VALUES(?,?,?,?,?,?)",
            (user_id, datetime.now().isoformat(timespec="seconds"), source_name, int(len(results)), int(len(findings)), json.dumps(safe_findings, default=str))
        )

def list_analyses(user_id: int):
    with connect() as conn:
        rows = conn.execute(
            "SELECT id,created_at,source_name,transaction_count,flagged_count FROM analyses WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def get_analysis(user_id: int, analysis_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE user_id=? AND id=?",
            (user_id, analysis_id)
        ).fetchone()
    if not row:
        return None
    return dict(row)
