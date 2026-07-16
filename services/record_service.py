from datetime import datetime
from database.db import get_connection


def save_code_record(code_text: str, language: str, explain_level: str,
                     ai_response: str, summary: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO code_records (code_text, language, explain_level, ai_response, summary) VALUES (?, ?, ?, ?, ?)",
        (code_text, language, explain_level, ai_response, summary),
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def list_code_records(keyword: str = None, language: str = None,
                      limit: int = 100, offset: int = 0) -> list:
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT id, code_text, language, explain_level, summary, created_at FROM code_records WHERE 1=1"
    params = []

    if keyword:
        query += " AND (code_text LIKE ? OR summary LIKE ? OR ai_response LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])

    if language:
        query += " AND language = ?"
        params.append(language)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_code_record(record_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM code_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_code_record(record_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM knowledge_points WHERE record_id = ?", (record_id,))
    cursor.execute("DELETE FROM review_tasks WHERE record_id = ?", (record_id,))
    cursor.execute("DELETE FROM code_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def save_knowledge_point(record_id: int, point_name: str, description: str, category: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO knowledge_points (record_id, point_name, description, category) VALUES (?, ?, ?, ?)",
        (record_id, point_name, description, category),
    )
    conn.commit()
    conn.close()


def list_knowledge_points(category: str = None, mastery_status: str = None,
                          limit: int = 200, offset: int = 0) -> list:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT kp.*, cr.code_text, cr.language as code_language
        FROM knowledge_points kp
        LEFT JOIN code_records cr ON kp.record_id = cr.id
        WHERE 1=1
    """
    params = []

    if category:
        query += " AND kp.category = ?"
        params.append(category)

    if mastery_status:
        query += " AND kp.mastery_status = ?"
        params.append(mastery_status)

    query += " ORDER BY kp.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def update_knowledge_status(point_id: int, mastery_status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE knowledge_points SET mastery_status = ? WHERE id = ?",
        (mastery_status, point_id),
    )
    conn.commit()
    conn.close()


def save_review_task(record_id: int, task_title: str, task_content: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO review_tasks (record_id, task_title, task_content) VALUES (?, ?, ?)",
        (record_id, task_title, task_content),
    )
    conn.commit()
    conn.close()


def list_review_tasks(status: str = None, limit: int = 100) -> list:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT rt.*, cr.code_text, cr.language
        FROM review_tasks rt
        LEFT JOIN code_records cr ON rt.record_id = cr.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND rt.status = ?"
        params.append(status)

    query += " ORDER BY rt.created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def mark_reviewed(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE review_tasks SET status = '已复习', reviewed_at = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id),
    )
    conn.commit()
    conn.close()


def delete_review_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM review_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_knowledge_point(point_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM knowledge_points WHERE id = ?", (point_id,))
    conn.commit()
    conn.close()


def get_distinct_languages() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT language FROM code_records WHERE language IS NOT NULL ORDER BY language")
    rows = [row["language"] for row in cursor.fetchall()]
    conn.close()
    return rows


def get_distinct_categories() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM knowledge_points WHERE category IS NOT NULL ORDER BY category")
    rows = [row["category"] for row in cursor.fetchall()]
    conn.close()
    return rows
