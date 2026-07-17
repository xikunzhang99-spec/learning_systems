import json
from database.db import get_connection
from config import settings


def generate_scene_script(topic_id, selected_item_ids, visual_style="", shot_count=5):
    from services.topic_service import get_topic
    from services.item_service import list_items as list_items_svc
    from services.ai_service import chat
    from prompts.scene_script_prompt import (
        build_scene_system_prompt,
        build_scene_user_prompt,
        parse_scene_response,
        PROMPT_VERSION,
    )

    topic = get_topic(topic_id)
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")

    all_items = list_items_svc(topic_id=topic_id, limit=2000)
    selected_items = [it for it in all_items if it["id"] in selected_item_ids]
    if not selected_items:
        raise ValueError("No valid items selected")

    visual_style = visual_style or "modern illustration, clean and colorful"
    shot_count = max(4, min(6, shot_count))

    system_prompt = build_scene_system_prompt(visual_style)
    user_prompt = build_scene_user_prompt(
        topic["title"], topic.get("description", ""), selected_items, shot_count
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    raw_response = chat(messages)

    scene_data = parse_scene_response(raw_response)

    conn = get_connection()
    cursor = conn.cursor()

    characters_json = json.dumps(scene_data.get("characters", []), ensure_ascii=False)
    model_name = f"{settings.AI_PROVIDER}:{_get_model_name()}"

    cursor.execute(
        """INSERT INTO scenes
           (topic_id, title, background, characters, learning_goal,
            visual_style, status, prompt_version, model, raw_response)
           VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)""",
        (
            topic_id,
            scene_data.get("scene_title", ""),
            scene_data.get("background", ""),
            characters_json,
            scene_data.get("learning_goal", ""),
            visual_style,
            PROMPT_VERSION,
            model_name,
            raw_response,
        ),
    )
    scene_id = cursor.lastrowid

    shots = scene_data.get("shots", [])
    for shot in shots:
        bound_ids = _match_highlight_items(
            shot.get("highlight_items", []), selected_items
        )
        cursor.execute(
            """INSERT INTO scene_shots
               (scene_id, "order", visual_description, character_action,
                dialogue, dialogue_zh, narration, bound_items)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scene_id,
                shot.get("order", 0),
                shot.get("visual_description", ""),
                shot.get("character_action", ""),
                shot.get("dialogue", ""),
                shot.get("dialogue_zh", ""),
                shot.get("narration", ""),
                json.dumps(bound_ids),
            ),
        )

    for item_id in selected_item_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO scene_items (scene_id, item_id) VALUES (?, ?)",
            (scene_id, item_id),
        )

    for item_id in selected_item_ids:
        cursor.execute(
            "UPDATE learning_items SET used_in_scene = 1 WHERE id = ?", (item_id,)
        )

    conn.commit()
    conn.close()

    return scene_id


def generate_scene_script_stream(topic_id, selected_item_ids, visual_style="",
                                  shot_count=5):
    from services.topic_service import get_topic
    from services.item_service import list_items as list_items_svc
    from services.ai_service import stream_chat
    from prompts.scene_script_prompt import (
        build_scene_system_prompt,
        build_scene_user_prompt,
        parse_scene_response,
        PROMPT_VERSION,
    )

    yield "Fetching topic and items..."
    topic = get_topic(topic_id)
    if not topic:
        yield "Error: Topic not found"
        return

    all_items = list_items_svc(topic_id=topic_id, limit=2000)
    selected_items = [it for it in all_items if it["id"] in selected_item_ids]
    if not selected_items:
        yield "Error: No valid items selected"
        return

    visual_style = visual_style or "modern illustration, clean and colorful"
    shot_count = max(4, min(6, shot_count))

    yield "Building prompts..."
    system_prompt = build_scene_system_prompt(visual_style)
    user_prompt = build_scene_user_prompt(
        topic["title"], topic.get("description", ""), selected_items, shot_count
    )

    yield "Calling AI to generate scene script..."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    full_response = ""
    try:
        for chunk in stream_chat(messages):
            full_response += chunk
            yield f"Receiving: {len(full_response)} chars..."
    except Exception as e:
        yield f"Error: AI call failed - {str(e)}"
        return

    yield "Parsing AI response..."
    try:
        scene_data = parse_scene_response(full_response)
    except ValueError as e:
        yield f"Error: Failed to parse AI response - {str(e)}"
        return

    yield "Saving to database..."
    conn = get_connection()
    cursor = conn.cursor()

    characters_json = json.dumps(scene_data.get("characters", []), ensure_ascii=False)
    model_name = f"{settings.AI_PROVIDER}:{_get_model_name()}"

    cursor.execute(
        """INSERT INTO scenes
           (topic_id, title, background, characters, learning_goal,
            visual_style, status, prompt_version, model, raw_response)
           VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)""",
        (
            topic_id,
            scene_data.get("scene_title", ""),
            scene_data.get("background", ""),
            characters_json,
            scene_data.get("learning_goal", ""),
            visual_style,
            PROMPT_VERSION,
            model_name,
            full_response,
        ),
    )
    scene_id = cursor.lastrowid

    shots = scene_data.get("shots", [])
    for shot in shots:
        bound_ids = _match_highlight_items(
            shot.get("highlight_items", []), selected_items
        )
        cursor.execute(
            """INSERT INTO scene_shots
               (scene_id, "order", visual_description, character_action,
                dialogue, dialogue_zh, narration, bound_items)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scene_id,
                shot.get("order", 0),
                shot.get("visual_description", ""),
                shot.get("character_action", ""),
                shot.get("dialogue", ""),
                shot.get("dialogue_zh", ""),
                shot.get("narration", ""),
                json.dumps(bound_ids),
            ),
        )

    for item_id in selected_item_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO scene_items (scene_id, item_id) VALUES (?, ?)",
            (scene_id, item_id),
        )

    for item_id in selected_item_ids:
        cursor.execute(
            "UPDATE learning_items SET used_in_scene = 1 WHERE id = ?", (item_id,)
        )

    conn.commit()
    conn.close()

    yield f"Done|scene_id={scene_id}"


def get_scene(scene_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    scene = dict(row)
    scene["characters"] = json.loads(scene.get("characters", "[]"))
    cursor.execute(
        'SELECT * FROM scene_shots WHERE scene_id = ? ORDER BY "order"', (scene_id,)
    )
    shots = [dict(r) for r in cursor.fetchall()]
    for shot in shots:
        shot["bound_items"] = json.loads(shot.get("bound_items", "[]"))
    scene["shots"] = shots
    conn.close()
    return scene


def list_scenes(topic_id=None, status=None, limit=50, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM scenes WHERE 1=1"
    params = []
    if topic_id is not None:
        query += " AND topic_id = ?"
        params.append(topic_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def update_scene_status(scene_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE scenes SET status = ? WHERE id = ?", (status, scene_id))
    conn.commit()
    conn.close()


def delete_scene(scene_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
    conn.commit()
    conn.close()


def get_scene_shots(scene_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM scene_shots WHERE scene_id = ? ORDER BY "order"', (scene_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    for row in rows:
        row["bound_items"] = json.loads(row.get("bound_items", "[]"))
    conn.close()
    return rows


def update_shot(shot_id, **kwargs):
    allowed = {"visual_description", "character_action", "dialogue",
               "dialogue_zh", "narration", "order"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return
    conn = get_connection()
    cursor = conn.cursor()
    sets = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [shot_id]
    cursor.execute(f"UPDATE scene_shots SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()


def reorder_shots(scene_id, shot_order):
    """shot_order: list of shot_ids in desired order"""
    conn = get_connection()
    cursor = conn.cursor()
    for i, shot_id in enumerate(shot_order, 1):
        cursor.execute(
            'UPDATE scene_shots SET "order" = ? WHERE id = ? AND scene_id = ?',
            (i, shot_id, scene_id),
        )
    conn.commit()
    conn.close()


def delete_shot(shot_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scene_shots WHERE id = ?", (shot_id,))
    conn.commit()
    conn.close()


def add_shot(scene_id, shot_data=None):
    shot_data = shot_data or {}
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX("order") FROM scene_shots WHERE scene_id = ?', (scene_id,))
    row = cursor.fetchone()
    next_order = (row[0] or 0) + 1
    cursor.execute(
        """INSERT INTO scene_shots
           (scene_id, "order", visual_description, character_action,
            dialogue, dialogue_zh, narration, bound_items)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            scene_id,
            shot_data.get("order", next_order),
            shot_data.get("visual_description", ""),
            shot_data.get("character_action", ""),
            shot_data.get("dialogue", ""),
            shot_data.get("dialogue_zh", ""),
            shot_data.get("narration", ""),
            json.dumps(shot_data.get("bound_items", [])),
        ),
    )
    shot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return shot_id


def regenerate_shot(scene_id, shot_id):
    """Regenerate a single shot using AI, keeping scene context."""
    from services.ai_service import chat
    from prompts.scene_script_prompt import parse_scene_response

    scene = get_scene(scene_id)
    if not scene:
        raise ValueError(f"Scene {scene_id} not found")

    shots = scene.get("shots", [])
    target_shot = next((s for s in shots if s["id"] == shot_id), None)
    if not target_shot:
        raise ValueError(f"Shot {shot_id} not found in scene {scene_id}")

    other_shots_context = "\n".join(
        f"Shot {s.get('order', '?')}: {s.get('dialogue', '')}"
        for s in shots
        if s["id"] != shot_id
    )

    prompt = f"""Regenerate a single shot for an English learning scene storyboard.

## Scene Context
Title: {scene.get('title', '')}
Background: {scene.get('background', '')}
Characters: {scene.get('characters', [])}

## Other Shots (for continuity)
{other_shots_context}

## Shot to Regenerate (Shot #{target_shot.get('order', '?')})
Original visual: {target_shot.get('visual_description', '')}
Original action: {target_shot.get('character_action', '')}

## Instructions
Return a single shot JSON object with the same order number:
```json
{{
  "order": {target_shot.get('order', 0)},
  "visual_description": "string",
  "character_action": "string",
  "dialogue": "string",
  "dialogue_zh": "string",
  "highlight_items": ["string"],
  "new_vocabulary": []
}}
```
Return ONLY the JSON object."""

    messages = [
        {"role": "system", "content": "You are a scriptwriter. Return only valid JSON."},
        {"role": "user", "content": prompt},
    ]
    raw = chat(messages)
    shot_data = parse_scene_response(raw)

    # If parse_scene_response returns a full scene dict, extract the shot
    if "shots" in shot_data:
        shot_data = shot_data["shots"][0] if shot_data["shots"] else shot_data

    update_shot(
        shot_id,
        visual_description=shot_data.get("visual_description", ""),
        character_action=shot_data.get("character_action", ""),
        dialogue=shot_data.get("dialogue", ""),
        dialogue_zh=shot_data.get("dialogue_zh", ""),
    )
    return raw


def regenerate_scene(scene_id):
    from services.ai_service import chat
    from prompts.scene_script_prompt import (
        build_scene_system_prompt,
        build_scene_user_prompt,
        parse_scene_response,
    )
    from services.item_service import list_items as list_items_svc

    old = get_scene(scene_id)
    if not old:
        raise ValueError(f"Scene {scene_id} not found")

    topic_id = old["topic_id"]
    all_items = list_items_svc(topic_id=topic_id, limit=2000)

    cursor_scene_items = get_connection()
    rows = cursor_scene_items.execute(
        "SELECT item_id FROM scene_items WHERE scene_id = ?", (scene_id,)
    ).fetchall()
    cursor_scene_items.close()
    selected_item_ids = [r["item_id"] for r in rows]
    selected_items = [it for it in all_items if it["id"] in selected_item_ids]

    system_prompt = build_scene_system_prompt(old.get("visual_style", ""))
    user_prompt = build_scene_user_prompt(
        "", "", selected_items, len(old.get("shots", [])) or 5
    )

    raw_response = chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    scene_data = parse_scene_response(raw_response)

    conn = get_connection()
    cursor = conn.cursor()

    characters_json = json.dumps(scene_data.get("characters", []), ensure_ascii=False)

    cursor.execute(
        """UPDATE scenes SET title = ?, background = ?, characters = ?,
           learning_goal = ?, version = version + 1, raw_response = ?,
           status = 'draft'
           WHERE id = ?""",
        (
            scene_data.get("scene_title", ""),
            scene_data.get("background", ""),
            characters_json,
            scene_data.get("learning_goal", ""),
            raw_response,
            scene_id,
        ),
    )

    cursor.execute("DELETE FROM scene_shots WHERE scene_id = ?", (scene_id,))

    shots = scene_data.get("shots", [])
    for shot in shots:
        bound_ids = _match_highlight_items(
            shot.get("highlight_items", []), selected_items
        )
        cursor.execute(
            """INSERT INTO scene_shots
               (scene_id, "order", visual_description, character_action,
                dialogue, dialogue_zh, narration, bound_items)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scene_id,
                shot.get("order", 0),
                shot.get("visual_description", ""),
                shot.get("character_action", ""),
                shot.get("dialogue", ""),
                shot.get("dialogue_zh", ""),
                shot.get("narration", ""),
                json.dumps(bound_ids),
            ),
        )

    conn.commit()
    conn.close()

    return scene_id


def get_scene_items_detail(scene_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT li.* FROM learning_items li
           JOIN scene_items si ON li.id = si.item_id
           WHERE si.scene_id = ?
           ORDER BY li.item_type, li.english""",
        (scene_id,),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def _match_highlight_items(highlights, selected_items):
    """Match highlight item strings to actual learning item IDs."""
    matched = []
    for h in highlights:
        h_lower = h.strip().lower()
        for item in selected_items:
            if item["english"].strip().lower() == h_lower:
                matched.append(item["id"])
                break
    return matched


def _get_model_name():
    provider = settings.AI_PROVIDER
    if provider == "deepseek":
        return settings.DEEPSEEK_MODEL
    if provider == "claude":
        return settings.CLAUDE_MODEL
    return settings.OPENAI_MODEL
