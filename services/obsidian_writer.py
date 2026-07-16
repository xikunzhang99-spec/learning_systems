import os
import re
from datetime import datetime
from config import settings


def _get_note_dir() -> str:
    vault = settings.OBSIDIAN_VAULT_PATH
    if not vault:
        raise ValueError("请在 .env 中设置 OBSIDIAN_VAULT_PATH")
    folder = settings.OBSIDIAN_NOTE_FOLDER
    note_dir = os.path.join(vault, folder)
    os.makedirs(note_dir, exist_ok=True)
    return note_dir


def _safe_filename(term: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "-", term)
    return safe.strip()


def note_exists(term: str) -> bool:
    note_dir = _get_note_dir()
    filename = f"{_safe_filename(term)}.md"
    return os.path.exists(os.path.join(note_dir, filename))


def save_note(term: str, markdown_content: str) -> str:
    note_dir = _get_note_dir()
    filename = f"{_safe_filename(term)}.md"
    filepath = os.path.join(note_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return filepath


def list_notes() -> list[dict]:
    note_dir = _get_note_dir()
    if not os.path.exists(note_dir):
        return []

    notes = []
    for f in sorted(os.listdir(note_dir), reverse=True):
        if f.endswith(".md"):
            filepath = os.path.join(note_dir, f)
            stat = os.stat(filepath)
            term = f[:-3]
            notes.append(
                {
                    "term": term,
                    "filepath": filepath,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )
    return notes


def read_note(term: str) -> str | None:
    note_dir = _get_note_dir()
    filename = f"{_safe_filename(term)}.md"
    filepath = os.path.join(note_dir, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def search_notes(keyword: str) -> list[dict]:
    note_dir = _get_note_dir()
    if not os.path.exists(note_dir):
        return []

    results = []
    keyword_lower = keyword.lower()
    for f in sorted(os.listdir(note_dir), reverse=True):
        if not f.endswith(".md"):
            continue
        filepath = os.path.join(note_dir, f)
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()

        term = f[:-3]
        if keyword_lower in term.lower() or keyword_lower in content.lower():
            lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]
            preview = " ".join(lines[:2])[:120] + "..." if lines else ""
            stat = os.stat(filepath)
            results.append(
                {
                    "term": term,
                    "filepath": filepath,
                    "preview": preview,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )
    return results
