"""
database.py
-----------
Small SQLite helper for storing and retrieving prediction history.
Demonstrates basic DBMS operations: CREATE TABLE, INSERT, SELECT, DELETE.
"""

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "heart_predictions.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            preferred_language TEXT NOT NULL DEFAULT 'en'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            note TEXT,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            age INTEGER, sex INTEGER, cp INTEGER, trestbps INTEGER,
            chol INTEGER, fbs INTEGER, restecg INTEGER, thalach INTEGER,
            exang INTEGER, oldpeak REAL, slope INTEGER, ca INTEGER, thal INTEGER,
            model_used TEXT NOT NULL,
            prediction INTEGER NOT NULL,
            probability REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()

    # Lightweight migration for anyone who already has an old DB file
    # (predictions table without user_id) -- add the column if missing.
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(predictions)").fetchall()]
    if "user_id" not in cols:
        conn.execute("ALTER TABLE predictions ADD COLUMN user_id INTEGER")
        conn.commit()

    user_cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "preferred_language" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT NOT NULL DEFAULT 'en'")
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(name: str, email: str, password_hash: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email.lower().strip(), password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return user_id


def get_user_by_email(email: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_user_language(user_id: int, lang: str):
    conn = get_connection()
    conn.execute("UPDATE users SET preferred_language = ? WHERE id = ?", (lang, user_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Predictions (scoped to a user)
# ---------------------------------------------------------------------------
def insert_prediction(user_id: int, patient: dict, model_used: str, prediction: int, probability: float):
    conn = get_connection()
    conn.execute("""
        INSERT INTO predictions
        (user_id, timestamp, age, sex, cp, trestbps, chol, fbs, restecg, thalach,
         exang, oldpeak, slope, ca, thal, model_used, prediction, probability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        patient["age"], patient["sex"], patient["cp"], patient["trestbps"],
        patient["chol"], patient["fbs"], patient["restecg"], patient["thalach"],
        patient["exang"], patient["oldpeak"], patient["slope"], patient["ca"], patient["thal"],
        model_used, prediction, probability
    ))
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return row_id


def get_predictions_for_user(user_id: int, limit: int = 200):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM predictions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_predictions_for_user(user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM predictions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Uploaded scan / test reports (scoped to a user)
# ---------------------------------------------------------------------------
def insert_report(user_id: int, filename: str, original_name: str, note: str):
    conn = get_connection()
    conn.execute("""
        INSERT INTO reports (user_id, filename, original_name, note, uploaded_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, filename, original_name, note, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return row_id


def get_reports_for_user(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_by_id(report_id: int):
    """Returns the report row regardless of owner -- callers MUST check the
    user_id field themselves before exposing the file, so a user can never
    be shown someone else's upload."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_report(report_id: int, user_id: int):
    """Deletes only if the report belongs to user_id -- returns True if a row
    was actually removed."""
    conn = get_connection()
    cur = conn.execute("DELETE FROM reports WHERE id = ? AND user_id = ?", (report_id, user_id))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted
