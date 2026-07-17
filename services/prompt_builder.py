"""Image Prompt Builder — converts scene/shot data into structured image prompts.

Separates shared (scene-level) and per-shot prompt components.
Integrates with config/visual_styles.py for style configuration.
"""

PROMPT_VERSION = "v1"


def build_scene_prompt(scene, style_id="american_comic"):
    """Build shared scene-level prompt context.

    Args:
        scene: dict from scene_service.get_scene() with keys like
               background, characters, title, learning_goal
        style_id: key from config/visual_styles.VISUAL_STYLES

    Returns:
        dict with shared_positive, shared_negative, character_desc,
        environment_desc, style_config, version
    """
    from config.visual_styles import (
        get_style, build_positive_prompt, build_negative_prompt,
    )

    style = get_style(style_id)
    style_pos = build_positive_prompt(style_id)
    style_neg = build_negative_prompt(style_id)

    characters = scene.get("characters", [])
    if isinstance(characters, str):
        import json
        try:
            characters = json.loads(characters)
        except (json.JSONDecodeError, TypeError):
            characters = []

    char_desc = _build_character_desc(characters)
    env_desc = _build_environment_desc(scene)

    shared_positive = (
        f"{scene.get('background', '')}. "
        f"{char_desc} "
        f"{env_desc} "
        f"{style_pos}"
    )

    return {
        "shared_positive": shared_positive.strip(),
        "shared_negative": style_neg,
        "character_desc": char_desc,
        "environment_desc": env_desc,
        "style_id": style_id,
        "style_name": style.get("name", style_id),
        "version": PROMPT_VERSION,
    }


def build_shot_prompt(shot, scene_prompt):
    """Build per-shot positive and negative prompts.

    Args:
        shot: dict from scene['shots'] with visual_description,
              character_action, order
        scene_prompt: dict returned by build_scene_prompt()

    Returns:
        dict with positive, negative, shot_index, visual_desc, character_action
    """
    shared_pos = scene_prompt.get("shared_positive", "")
    shared_neg = scene_prompt.get("shared_negative", "")
    visual = shot.get("visual_description", "")
    action = shot.get("character_action", "")

    # Per-shot specifics
    shot_specific = []
    if action:
        shot_specific.append(action)
    if visual:
        shot_specific.append(visual)

    shot_pos = f"{shared_pos}. {' — '.join(shot_specific)}"

    # No text rule
    no_text_rule = (
        "no text, no letters, no words, no captions, no subtitles, "
        "no speech bubbles, no dialogue boxes, no typography, "
        "no watermark, no logo, no UI elements"
    )
    shot_neg = f"{shared_neg}, {no_text_rule}"

    return {
        "positive": shot_pos.strip(),
        "negative": shot_neg,
        "shot_order": shot.get("order", 0),
        "visual_desc": visual,
        "character_action": action,
    }


def build_all_shot_prompts(scene, style_id="american_comic"):
    """Build prompts for all shots in a scene.

    Args:
        scene: dict from scene_service.get_scene()
        style_id: visual style key

    Returns:
        list of dicts, one per shot, each with positive, negative, shot_order
    """
    scene_prompt = build_scene_prompt(scene, style_id)
    shots = scene.get("shots", [])

    results = []
    for shot in shots:
        shot_prompt = build_shot_prompt(shot, scene_prompt)
        results.append(shot_prompt)

    return results


def validate_prompt(prompt_dict):
    """Validate a shot prompt dict. Returns list of issues (empty = valid)."""
    issues = []

    if not prompt_dict.get("positive"):
        issues.append("Missing positive prompt")
    if not prompt_dict.get("negative"):
        issues.append("Missing negative prompt")

    pos = prompt_dict.get("positive", "").lower()
    neg = prompt_dict.get("negative", "").lower()

    # Detect dialogue-generating instructions in image prompt
    banned = [
        "dialogue", "caption", "subtitle", "speech bubble",
        "text box", "words on", "letters on", "written",
    ]
    for word in banned:
        if word in pos:
            issues.append(
                f"Image prompt contains '{word}' — may generate text in image"
            )

    # Verify negative prompt includes text prohibition
    required_neg = ["no text", "no letters", "no words"]
    for kw in required_neg:
        if kw not in neg:
            issues.append(f"Negative prompt missing '{kw}'")
            break

    return issues


def validate_scene_prompts(all_prompts, scene):
    """Validate all prompts for a scene. Checks consistency across shots.

    Returns list of issues.
    """
    issues = []

    if not all_prompts:
        issues.append("No prompts generated")
        return issues

    shots = scene.get("shots", [])
    if len(all_prompts) != len(shots):
        issues.append(
            f"Shot count mismatch: {len(all_prompts)} prompts vs {len(shots)} shots"
        )

    # Check character names consistent
    characters = scene.get("characters", [])
    if isinstance(characters, str):
        import json
        try:
            characters = json.loads(characters)
        except (json.JSONDecodeError, TypeError):
            characters = []

    for i, prompt in enumerate(all_prompts):
        shot_issues = validate_prompt(prompt)
        for issue in shot_issues:
            issues.append(f"Shot {i+1}: {issue}")

    return issues


def _build_character_desc(characters):
    """Build character description string."""
    if not characters:
        return ""
    if isinstance(characters, list):
        descs = []
        for c in characters:
            if isinstance(c, dict):
                descs.append(f"{c.get('name', 'character')}: {c.get('description', '')}")
            else:
                descs.append(str(c))
        return "Characters: " + "; ".join(descs) + ". "
    return f"Character: {characters}. "


def _build_environment_desc(scene):
    """Build environment description from scene background."""
    bg = scene.get("background", "")
    if bg:
        return f"Setting: {bg}. "
    return ""
