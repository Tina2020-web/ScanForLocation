import os
import psycopg2
import psycopg2.extras
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vin_location (
                    id            SERIAL PRIMARY KEY,
                    vin           TEXT   UNIQUE NOT NULL,
                    location_code TEXT   NOT NULL,
                    updated_at    TEXT   NOT NULL
                )
            """)
        conn.commit()

def lookup_vin(vin: str):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM vin_location WHERE vin = %s", (vin.strip().upper(),)
            )
            row = cur.fetchone()
    return dict(row) if row else None

def upsert_vin(vin: str, location_code: str):
    now = datetime.now().isoformat()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vin_location (vin, location_code, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (vin) DO UPDATE SET
                    location_code = EXCLUDED.location_code,
                    updated_at    = EXCLUDED.updated_at
            """, (vin.strip().upper(), location_code.strip(), now))
        conn.commit()

def get_all():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM vin_location ORDER BY updated_at DESC")
            rows = cur.fetchall()
    return [dict(r) for r in rows]

def delete_vin(vin: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM vin_location WHERE vin = %s", (vin.strip().upper(),)
            )
        conn.commit()
