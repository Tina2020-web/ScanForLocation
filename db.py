import sqlite3
from datetime import datetime

DB_PATH = "vin_location.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vin_location (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                vin           TEXT    UNIQUE NOT NULL,
                location_code TEXT    NOT NULL,
                updated_at    TEXT    NOT NULL
            )
        """)
        conn.commit()

def lookup_vin(vin: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM vin_location WHERE vin = ?", (vin.strip().upper(),)
        ).fetchone()
    return dict(row) if row else None

def upsert_vin(vin: str, location_code: str):
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO vin_location (vin, location_code, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(vin) DO UPDATE SET
                location_code = excluded.location_code,
                updated_at    = excluded.updated_at
        """, (vin.strip().upper(), location_code.strip(), now))
        conn.commit()

def get_all():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM vin_location ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]

def delete_vin(vin: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM vin_location WHERE vin = ?", (vin.strip().upper(),))
        conn.commit()
