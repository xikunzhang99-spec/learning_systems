import json
import re

PROMPT_VERSION = "v1"

SCENE_OUTPUT_SCHEMA = """
{
  "scene_title": "string (English scene title)",
  "scene_title_zh": "string (Chinese scene title)",
  "background": "string (2-3 sentences describing setting/time/place)",
  "characters": ["string (character name and brief description)", ...],
  "learning_goal": "string (what the learner should take away)",
  "shots": [
    {
      "order": 1,
      "visual_description": "string (detailed visual description for illustration)",
      "character_action": "string (what characters are doing in this shot)",
      "dialogue": "string (actual English dialogue spoken in this shot)",
      "dialogue_zh": "string (Chinese translation of the dialogue)",
      "narration": "string (optional scene narration or context, describing what happens visually, can be empty)",
      "highlight_items": ["string (english word/phrase from the selected items)", ...],
      "new_vocabulary": [
        {"english": "string", "chinese": "string", "context": "string"}
      ]
    }
  ],
  "grammar_notes": [
    {"pattern": "string", "explanation": "string", "example": "string"}
  ],
  "cultural_note": "string (optional cultural context, can be empty)"
}
"""


def build_scene_system_prompt(visual_style="modern illustration"):
    return f"""You are an experienced ESL teacher and scriptwriter who creates engaging, natural English learning scenes for Chinese learners.

Your task: given a topic and a list of English words/phrases/expressions the learner wants to practice, write a short scene script that weaves those items naturally into a coherent story.

The output is a structured JSON scene script with 4-6 sequential shots (like a storyboard). Each shot advances the story and contains dialogue that uses the learning items.

## Visual Style
{visual_style}

## Scene Structure
- Start with a clear setting and character introduction
- Develop the situation with natural interaction
- Include a small problem, question, or turning point
- End with resolution or takeaway
- Use 4-6 sequential shots

## Rules
1. Weave the provided learning items NATURALLY into the dialogue and scene. Never force them or list them awkwardly.
2. Every "highlight_items" entry MUST be an exact match of one of the provided learning items' English text.
3. If a learning item doesn't fit naturally, include it in "unused_items" with a brief reason rather than forcing it.
4. Dialogue should sound like real spoken English, not textbook English.
5. Provide Chinese translations for all dialogue (dialogue_zh).
6. Keep each shot focused on one moment or interaction.
7. The visual_description should be detailed enough for an illustrator to draw the scene.
8. All text fields besides dialogue, scene_title, and english fields should be in Chinese.

## Output Format
Return ONLY valid JSON matching this schema exactly:

```json
{SCENE_OUTPUT_SCHEMA}
```

Do NOT include markdown code fences or any text outside the JSON object."""


def build_scene_user_prompt(topic_title, topic_description, selected_items, shot_count=5):
    items_table = _format_items_table(selected_items)
    return f"""## Topic
**Title**: {topic_title}
**Description**: {topic_description or 'N/A'}

## Learning Items to Include
The learner wants to practice these specific items. Weave them naturally into the scene.

{items_table}

## Shot Count
Generate exactly {shot_count} shots (sequential storyboard frames).

## Instructions
1. Create a natural, engaging scene that feels like a real conversation or situation.
2. Use the items above in the dialogue and character actions.
3. Match highlight_items to the EXACT English text from the table above.
4. Generate {shot_count} sequential shots that tell a complete mini-story.
5. Return ONLY the JSON object, no other text."""


def _format_items_table(items):
    lines = []
    for i, item in enumerate(items, 1):
        itype = item.get("item_type", "word")
        english = item.get("english", "")
        chinese = item.get("chinese", "")
        notes = item.get("notes", "")
        extra = f" | notes: {notes}" if notes else ""
        lines.append(f"{i}. [{itype}] {english} — {chinese}{extra}")
    return "\n".join(lines)


def parse_scene_response(raw_response):
    raw = raw_response.strip()

    # Try direct JSON parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { to last }
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from AI response. Raw: {raw[:500]}...")


def validate_scene_data(scene_data, selected_item_ids, selected_items):
    """Validate parsed scene data. Returns list of issues (empty = valid)."""
    issues = []

    if not scene_data.get("scene_title"):
        issues.append("Missing scene_title")

    shots = scene_data.get("shots", [])
    if not shots:
        issues.append("No shots generated")
    elif len(shots) < 3:
        issues.append(f"Too few shots: {len(shots)}, expected at least 3")
    elif len(shots) > 8:
        issues.append(f"Too many shots: {len(shots)}, expected at most 8")

    for shot in shots:
        order = shot.get("order", "?")
        if not shot.get("dialogue"):
            issues.append(f"Shot {order}: missing dialogue")

    # Check item coverage
    item_englishes = {item["english"].lower() for item in selected_items}
    highlighted = set()
    for shot in shots:
        for h in shot.get("highlight_items", []):
            highlighted.add(h.lower())

    missing = item_englishes - highlighted
    if missing:
        issues.append(f"Items not used in any shot: {', '.join(sorted(missing))}")

    return issues
