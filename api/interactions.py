"""SQLite-backed interaction logging.

Records searches and user clicks (view details / compare / show more) so the
data can later power real ML (collaborative filtering, learning-to-rank).
Kept separate from model/recommend.py on purpose: the engine stays pure.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

# data/interactions.db relative to the project root
_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "interactions.db",
)

# Tests point this at a temp file via set_db_path().
DB_PATH = _DEFAULT_DB

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS search_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    client_sid TEXT,
    budget TEXT,
    purpose TEXT,
    min_ram REAL,
    min_storage REAL,
    storage_type TEXT,
    brand TEXT,
    min_cpu_tier INTEGER,
    min_gpu_tier INTEGER,
    min_screen REAL,
    touchscreen INTEGER DEFAULT 0,
    dedicated_gpu INTEGER DEFAULT 0,
    top_n INTEGER,
    status TEXT,
    results_shown INTEGER,
    top_score REAL
);
CREATE TABLE IF NOT EXISTS click_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    client_sid TEXT,
    search_row_id INTEGER,
    action TEXT NOT NULL,
    position INTEGER,
    score REAL,
    brand TEXT,
    cpu_model TEXT,
    gpu_model TEXT,
    ram_gb REAL,
    storage_gb REAL,
    storage_type TEXT,
    price_npr REAL,
    os TEXT,
    screen_size REAL
);
"""


def set_db_path(path):
    """Override the database location (used by the test suite)."""
    global DB_PATH
    DB_PATH = path


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)  # idempotent; guarantees tables exist
    return conn


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def insert_search(client_sid=None, **fields):
    """Log one search request. Returns the new row id."""
    row = (
        _now_iso(),
        client_sid,
        fields.get("budget"),
        fields.get("purpose"),
        fields.get("min_ram"),
        fields.get("min_storage"),
        fields.get("storage_type"),
        fields.get("brand"),
        fields.get("min_cpu_tier"),
        fields.get("min_gpu_tier"),
        fields.get("min_screen"),
        int(bool(fields.get("touchscreen", False))),
        int(bool(fields.get("dedicated_gpu", False))),
        fields.get("top_n"),
        fields.get("status"),
        fields.get("results_shown"),
        fields.get("top_score"),
    )
    with _lock, _connect() as conn:
        cur = conn.execute(
            """INSERT INTO search_events (
                   ts, client_sid, budget, purpose, min_ram, min_storage,
                   storage_type, brand, min_cpu_tier, min_gpu_tier, min_screen,
                   touchscreen, dedicated_gpu, top_n, status, results_shown, top_score
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
        return cur.lastrowid


def insert_click(client_sid=None, **fields):
    """Log one user interaction. Returns the new row id."""
    row = (
        _now_iso(),
        client_sid,
        fields.get("search_row_id"),
        fields.get("action"),
        fields.get("position"),
        fields.get("score"),
        fields.get("brand"),
        fields.get("cpu_model"),
        fields.get("gpu_model"),
        fields.get("ram_gb"),
        fields.get("storage_gb"),
        fields.get("storage_type"),
        fields.get("price_npr"),
        fields.get("os"),
        fields.get("screen_size"),
    )
    with _lock, _connect() as conn:
        cur = conn.execute(
            """INSERT INTO click_events (
                   ts, client_sid, search_row_id, action, position, score,
                   brand, cpu_model, gpu_model, ram_gb, storage_gb,
                   storage_type, price_npr, os, screen_size
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
        return cur.lastrowid


def log_stats():
    """Small summary for sanity-checking that logging works."""
    with _lock, _connect() as conn:
        searches = conn.execute("SELECT COUNT(*) FROM search_events").fetchone()[0]
        clicks = conn.execute("SELECT COUNT(*) FROM click_events").fetchone()[0]
        by_action = dict(
            conn.execute(
                "SELECT action, COUNT(*) FROM click_events GROUP BY action"
            ).fetchall()
        )
        recent_clicks = [
            dict(zip(("ts", "action", "brand", "cpu_model", "position"), r))
            for r in conn.execute(
                """SELECT ts, action, brand, cpu_model, position
                   FROM click_events ORDER BY id DESC LIMIT 10"""
            ).fetchall()
        ]
    return {
        "total_searches": searches,
        "total_clicks": clicks,
        "clicks_by_action": by_action,
        "recent_clicks": recent_clicks,
    }


def export_json():
    """Dump every logged row as JSON (handy for offline ML notebooks)."""
    with _lock, _connect() as conn:
        conn.row_factory = sqlite3.Row
        searches = [dict(r) for r in conn.execute("SELECT * FROM search_events")]
        clicks = [dict(r) for r in conn.execute("SELECT * FROM click_events")]
    return json.dumps({"searches": searches, "clicks": clicks}, indent=2)
