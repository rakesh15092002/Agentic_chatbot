import sqlite3
from pathlib import Path

DB_PATH = Path("chatbot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Rows behave like dictionaries
    return conn

def init_db():
    """
    Create tables for threads and messages if they don't exist
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Threads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS threads (
        id TEXT PRIMARY KEY,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(thread_id) REFERENCES threads(id)
    )
    """)

    conn.commit()
    conn.close()
