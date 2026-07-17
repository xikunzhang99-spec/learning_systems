import json
import re

PROMPT_VERSION = "v1"


def build_lookup_system_prompt():
    return """You are an expert English teacher and lexicographer helping a Chinese learner build their personal English expression library.

Your task: given a word, phrase, or sentence in English or Chinese, return a structured learning entry.

## Input Types
- Single English word: "accumulate"
- English phrase: "accumulate experience"
- English sentence: "AI can interact with the physical world."
- Chinese word/phrase: "积累经验"
- Chinese sentence: "人工智能可以积累经验"

## Rules
1. If input is Chinese, translate to the most natural, commonly-used English equivalent. Do NOT do word-for-word translation.
2. If input is English, check for obvious spelling/grammar issues. Suggest corrections if needed but do not silently change meaning.
3. Classify as one of: "word", "phrase", "expression", "sentence".
   - word: single dictionary word
   - phrase: 2+ words forming a natural collocation or idiom
   - expression: fixed idiomatic expression or set phrase
   - sentence: complete sentence with subject and predicate
4. The example sentence must use the word naturally in context.
5. Keep notes concise and practical (usage tips, formality, common contexts).

## Output Format
Return ONLY valid JSON:
```json
{
  "english": "string (the standard English form)",
  "chinese": "string (Chinese translation/meaning)",
  "item_type": "word|phrase|expression|sentence",
  "notes": "string (brief usage note, register, context)",
  "example_en": "string (one natural example sentence in English)",
  "example_zh": "string (Chinese translation of the example)",
  "related_words": "string (comma-separated synonyms or related expressions, empty if none)",
  "confidence": "high|medium|low"
}
```"""


def build_lookup_user_prompt(text):
    return f"""Look up the following and return a structured learning entry:

Input: {text}

Return ONLY the JSON object with no additional text."""


def parse_lookup_response(raw):
    raw = raw.strip()
    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try markdown code fence
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try first { to last }
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse lookup response. Raw: {raw[:300]}...")


def validate_lookup_result(data):
    """Validate lookup result. Returns list of issues (empty = valid)."""
    issues = []
    if not data.get("english"):
        issues.append("Missing english field")
    if not data.get("chinese"):
        issues.append("Missing chinese field")
    valid_types = {"word", "phrase", "expression", "sentence"}
    if data.get("item_type") not in valid_types:
        issues.append(f"Invalid item_type: {data.get('item_type')}")
    return issues
