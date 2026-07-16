import subprocess
import os
import sys
import glob
import time
from pathlib import Path
from config import settings
from database.db import get_connection


def generate_theme_stream(theme_name, style):
    """Run Node.js CLI and yield log lines in real time. Returns (output_path, logs)."""
    node_script = os.path.join(settings.NODE_SRC_DIR, "index.js")
    cmd = ["node", node_script, "--theme", theme_name, "--style", style]

    proc = subprocess.Popen(
        cmd,
        cwd=settings.BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    logs = []
    for line in proc.stdout:
        line_clean = line.rstrip()
        logs.append(line_clean)
        yield line_clean

    proc.wait()

    result_path = None
    for line in logs:
        if "Output:" in line:
            result_path = line.split("Output:", 1)[-1].strip()
            break

    if result_path and os.path.isfile(result_path):
        save_generation(theme_name, style, result_path)

    return result_path, proc.returncode


def save_generation(theme_name, style, output_path):
    conn = get_connection()
    conn.execute(
        "INSERT INTO theme_generations (theme_name, style, output_path) VALUES (?, ?, ?)",
        (theme_name, style, output_path),
    )
    conn.commit()
    conn.close()


def list_generations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, theme_name, style, output_path, created_at FROM theme_generations ORDER BY created_at DESC"
    ).fetchall()
    # Also scan for orphaned files
    existing_paths = {row["output_path"] for row in rows}
    for f in sorted(glob.glob(os.path.join(settings.OUTPUT_DIR, "theme-*.html")), key=os.path.getmtime, reverse=True):
        if f not in existing_paths and os.path.isfile(f):
            theme = Path(f).stem.replace("theme-", "").replace("-", " ").title()
            save_generation(theme, "unknown", f)
    # Re-query after possible inserts
    rows = conn.execute(
        "SELECT id, theme_name, style, output_path, created_at FROM theme_generations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_generation(gen_id):
    conn = get_connection()
    conn.execute("DELETE FROM theme_generations WHERE id = ?", (gen_id,))
    conn.commit()
    conn.close()
