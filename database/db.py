import sqlite3
import os
from config.settings import DATABASE_PATH


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS code_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_text TEXT NOT NULL,
            language TEXT,
            explain_level TEXT,
            ai_response TEXT,
            summary TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            point_name TEXT,
            description TEXT,
            category TEXT,
            mastery_status TEXT DEFAULT '未掌握',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES code_records(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            task_title TEXT,
            task_content TEXT,
            status TEXT DEFAULT '待复习',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            FOREIGN KEY (record_id) REFERENCES code_records(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS theme_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_name TEXT NOT NULL,
            style TEXT NOT NULL,
            output_path TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
