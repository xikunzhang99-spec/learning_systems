"""Deprecated: Old theme-based scene generation via Node.js subprocess.

This module is kept for backward compatibility only.
All functions raise NotImplementedError.

Use the new Topic → Learning Items → Scene workflow via scene_service.py.
"""


def generate_theme_stream(theme_name, style):
    raise NotImplementedError(
        "Old scene generation has been removed. "
        "Use the new Topic → Learning Items → Scene workflow in the English Learning page."
    )


def save_generation(theme_name, style, output_path):
    raise NotImplementedError("Old scene generation has been removed.")


def list_generations():
    raise NotImplementedError("Old scene generation has been removed.")


def delete_generation(gen_id):
    raise NotImplementedError("Old scene generation has been removed.")
