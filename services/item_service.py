from database.db import get_connection


def create_item(topic_id, english, chinese, item_type="word", notes="",
                original_text="", corrected_text="", source="manual"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO learning_items
           (topic_id, english, chinese, item_type, notes,
            original_text, corrected_text, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (topic_id, english, chinese, item_type, notes,
         original_text, corrected_text, source),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def create_items_batch(items):
    """items: list of dicts with topic_id, english, chinese, item_type, notes, etc."""
    conn = get_connection()
    cursor = conn.cursor()
    count = 0
    for item in items:
        cursor.execute(
            """INSERT INTO learning_items
               (topic_id, english, chinese, item_type, notes,
                original_text, corrected_text, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.get("topic_id"),
                item.get("english", ""),
                item.get("chinese", ""),
                item.get("item_type", "word"),
                item.get("notes", ""),
                item.get("original_text", ""),
                item.get("corrected_text", ""),
                item.get("source", "manual"),
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def update_item(item_id, **kwargs):
    allowed = {"english", "chinese", "item_type", "notes", "mastery_level",
               "original_text", "corrected_text", "used_in_scene"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return
    conn = get_connection()
    cursor = conn.cursor()
    sets = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    cursor.execute(f"UPDATE learning_items SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM learning_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learning_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_items(topic_id=None, item_type=None, mastery_level=None, keyword=None,
               used_in_scene=None, limit=500, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM learning_items WHERE 1=1"
    params = []
    if topic_id is not None:
        query += " AND topic_id = ?"
        params.append(topic_id)
    if item_type:
        query += " AND item_type = ?"
        params.append(item_type)
    if mastery_level is not None:
        query += " AND mastery_level = ?"
        params.append(mastery_level)
    if keyword:
        query += " AND (english LIKE ? OR chinese LIKE ? OR notes LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])
    if used_in_scene is not None:
        query += " AND used_in_scene = ?"
        params.append(1 if used_in_scene else 0)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def update_mastery(item_id, mastery_level):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE learning_items SET mastery_level = ? WHERE id = ?",
        (mastery_level, item_id),
    )
    conn.commit()
    conn.close()


def get_item_counts_by_topic(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT item_type, COUNT(*) as cnt
           FROM learning_items WHERE topic_id = ?
           GROUP BY item_type""",
        (topic_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    counts = {"word": 0, "phrase": 0, "expression": 0, "sentence": 0}
    for row in rows:
        counts[row["item_type"]] = row["cnt"]
    return counts


def search_items(keyword, topic_id=None):
    return list_items(topic_id=topic_id, keyword=keyword, limit=200)
