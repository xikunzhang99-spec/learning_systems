from prompts.code_tutor_prompt import build_prompt_by_level
from services.ai_service import chat, stream_chat


def explain_code(code: str, language: str, explain_level: str) -> dict:
    prompt = build_prompt_by_level(code, language, explain_level)
    ai_response = chat([
        {"role": "system", "content": "你是一个非常有耐心的编程学习教练，用中文回答。"},
        {"role": "user", "content": prompt},
    ])

    summary = _extract_summary(ai_response, code)

    return {
        "code": code,
        "language": language,
        "explain_level": explain_level,
        "ai_response": ai_response,
        "summary": summary,
    }


def explain_code_stream(code: str, language: str, explain_level: str):
    prompt = build_prompt_by_level(code, language, explain_level)
    return stream_chat([
        {"role": "system", "content": "你是一个非常有耐心的编程学习教练，用中文回答。"},
        {"role": "user", "content": prompt},
    ])


def _extract_summary(ai_response: str, code: str) -> str:
    lines = ai_response.strip().split("\n")
    capture = False
    for line in lines:
        stripped = line.strip()
        if "整体" in stripped and ("作用" in stripped or "做" in stripped):
            capture = True
            continue
        if capture and stripped.startswith("##"):
            break
        if capture and stripped and len(stripped) > 10:
            return stripped
    return code[:80]
