import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "fake_news.db")

def get_connection():
    """Returns a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database schema if not already present."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type TEXT NOT NULL,
            original_text TEXT,
            extracted_text TEXT,
            prediction TEXT NOT NULL,
            confidence REAL NOT NULL,
            model_used TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_scan(
    input_type: str,
    original_text: Optional[str],
    extracted_text: Optional[str],
    prediction: str,
    confidence: float,
    model_used: str
) -> int:
    """Insert a new verification record into the database."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO scan_history (
            input_type, original_text, extracted_text, prediction, confidence, model_used, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (input_type, original_text or '', extracted_text or '', prediction, round(confidence, 2), model_used, now_str))
    conn.commit()
    scan_id = cursor.lastrowid
    conn.close()
    return scan_id

def get_history(search: Optional[str] = None, filter_pred: Optional[str] = None, filter_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve scan history with optional search query and category filters."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM scan_history WHERE 1=1"
    params = []

    if search:
        query += " AND (original_text LIKE ? OR extracted_text LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])

    if filter_pred and filter_pred.upper() != 'ALL':
        query += " AND prediction = ?"
        params.append(filter_pred.upper())

    if filter_type and filter_type.upper() != 'ALL':
        query += " AND input_type = ?"
        params.append(filter_type.lower())

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

def get_scan(scan_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single scan record by ID."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scan_history WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_scan(scan_id: int) -> bool:
    """Delete a scan record from the database."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scan_history WHERE id = ?", (scan_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
