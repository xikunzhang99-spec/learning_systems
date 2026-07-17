from services.ai_service import chat
from prompts.lookup_prompt import (
    build_lookup_system_prompt,
    build_lookup_user_prompt,
    parse_lookup_response,
    PROMPT_VERSION,
)


def lookup_expression(text):
    """Query AI to identify/translate an English or Chinese expression.

    Args:
        text: English or Chinese word, phrase, or sentence.

    Returns:
        dict with keys: english, chinese, item_type, notes,
                        example_en, example_zh, related_words, confidence
    """
    text = text.strip()
    if not text:
        return None

    system_prompt = build_lookup_system_prompt()
    user_prompt = build_lookup_user_prompt(text)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_response = chat(messages)
    result = parse_lookup_response(raw_response)

    # Ensure all expected fields exist
    result.setdefault("english", text)
    result.setdefault("chinese", "")
    result.setdefault("item_type", "word")
    result.setdefault("notes", "")
    result.setdefault("example_en", "")
    result.setdefault("example_zh", "")
    result.setdefault("related_words", "")
    result.setdefault("confidence", "medium")
    result["_raw"] = raw_response
    result["_prompt_version"] = PROMPT_VERSION

    return result


def batch_lookup(texts):
    """Look up multiple expressions sequentially.

    Args:
        texts: list of strings to look up.

    Returns:
        list of (text, result_dict or error_string) tuples.
    """
    results = []
    for text in texts:
        text = text.strip()
        if not text:
            continue
        try:
            result = lookup_expression(text)
            results.append({"input": text, "result": result, "error": None})
        except Exception as e:
            results.append({"input": text, "result": None, "error": str(e)})
    return results
