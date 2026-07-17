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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            english TEXT NOT NULL,
            chinese TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT 'word',
            notes TEXT DEFAULT '',
            mastery_level INTEGER DEFAULT 0,
            original_text TEXT DEFAULT '',
            corrected_text TEXT DEFAULT '',
            source TEXT DEFAULT 'manual',
            used_in_scene INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            background TEXT DEFAULT '',
            characters TEXT DEFAULT '[]',
            learning_goal TEXT DEFAULT '',
            template TEXT DEFAULT 'grid4',
            visual_style TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            version INTEGER DEFAULT 1,
            prompt_version TEXT DEFAULT 'v1',
            model TEXT DEFAULT '',
            raw_response TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scene_shots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scene_id INTEGER NOT NULL,
            "order" INTEGER NOT NULL,
            visual_description TEXT DEFAULT '',
            character_action TEXT DEFAULT '',
            dialogue TEXT DEFAULT '',
            dialogue_zh TEXT DEFAULT '',
            bound_items TEXT DEFAULT '[]',
            image_path TEXT DEFAULT '',
            prompt_positive TEXT DEFAULT '',
            prompt_negative TEXT DEFAULT '',
            narration TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scene_items (
            scene_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            PRIMARY KEY (scene_id, item_id),
            FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES learning_items(id) ON DELETE CASCADE
        )
    """)

    # Migrations for existing databases
    for col, col_type in [
        ("image_path", "TEXT DEFAULT ''"),
        ("prompt_positive", "TEXT DEFAULT ''"),
        ("prompt_negative", "TEXT DEFAULT ''"),
        ("narration", "TEXT DEFAULT ''"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE scene_shots ADD COLUMN {col} {col_type}")
        except Exception:
            pass

    conn.commit()
    conn.close()
