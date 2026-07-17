from datetime import datetime
from database.db import get_connection


def create_topic(title, description="", tags=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO topics (title, description, tags) VALUES (?, ?, ?)",
        (title, description, tags),
    )
    conn.commit()
    topic_id = cursor.lastrowid
    conn.close()
    return topic_id


def update_topic(topic_id, title=None, description=None, tags=None, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    fields = {}
    if title is not None:
        fields["title"] = title
    if description is not None:
        fields["description"] = description
    if tags is not None:
        fields["tags"] = tags
    if status is not None:
        fields["status"] = status
    if not fields:
        conn.close()
        return
    fields["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sets = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [topic_id]
    cursor.execute(f"UPDATE topics SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_topic(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()


def get_topic(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_topics(keyword=None, tag=None, status="active", limit=100, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM topics WHERE 1=1"
    params = []
    if keyword:
        query += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])
    if tag:
        query += " AND tags LIKE ?"
        params.append(f"%{tag}%")
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_topic_stats(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as item_count FROM learning_items WHERE topic_id = ?",
        (topic_id,),
    )
    item_count = cursor.fetchone()["item_count"]
    cursor.execute(
        "SELECT COUNT(*) as scene_count FROM scenes WHERE topic_id = ?",
        (topic_id,),
    )
    scene_count = cursor.fetchone()["scene_count"]
    conn.close()
    return {"item_count": item_count, "scene_count": scene_count}


def get_all_tags():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tags FROM topics WHERE tags != ''")
    rows = cursor.fetchall()
    conn.close()
    tags_set = set()
    for row in rows:
        for tag in row["tags"].split(","):
            tag = tag.strip()
            if tag:
                tags_set.add(tag)
    return sorted(tags_set)
