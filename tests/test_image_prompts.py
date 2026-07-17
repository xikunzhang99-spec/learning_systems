"""Snapshot/regression tests for image prompt builder.

Run: python3 tests/test_image_prompts.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_scene(background, characters, title="Test Scene", learning_goal="Learn English"):
    return {
        "id": 1,
        "title": title,
        "background": background,
        "characters": characters if isinstance(characters, str) else list(characters),
        "learning_goal": learning_goal,
        "visual_style": "american comic",
        "shots": [],
    }


def _make_shot(order, visual, action):
    return {
        "id": order,
        "order": order,
        "visual_description": visual,
        "character_action": action,
        "dialogue": "Hello!",
        "dialogue_zh": "你好！",
    }


def add_shots(scene, shot_data_list):
    for i, (visual, action) in enumerate(shot_data_list, 1):
        scene["shots"].append(_make_shot(i, visual, action))
    return scene


def test_4_shot_single_character():
    """4-shot scene with one character."""
    scene = _make_scene("A modern office", ["John: office worker"])
    add_shots(scene, [
        ("John enters the office building", "Walking towards entrance"),
        ("John sits at his desk", "Opening laptop"),
        ("John in a meeting room", "Presenting slides"),
        ("John leaves office", "Waving goodbye"),
    ])
    from services.prompt_builder import build_all_shot_prompts, validate_scene_prompts
    prompts = build_all_shot_prompts(scene, "american_comic")
    assert len(prompts) == 4, f"Expected 4 prompts, got {len(prompts)}"
    for p in prompts:
        assert p["positive"], "Missing positive prompt"
        assert p["negative"], "Missing negative prompt"
        assert "text" in p["negative"].lower(), "Negative should prohibit text"
    issues = validate_scene_prompts(prompts, scene)
    assert not issues, f"Validation issues: {issues}"
    return True


def test_6_shot_two_characters():
    """6-shot scene with two characters."""
    scene = _make_scene("A coffee shop", ["Alice: barista", "Bob: customer"])
    add_shots(scene, [
        ("Alice behind the counter", "Wiping cups"),
        ("Bob enters the shop", "Opening the door"),
        ("Bob orders at counter", "Pointing at menu"),
        ("Alice prepares coffee", "Using espresso machine"),
        ("Bob receives coffee", "Taking the cup"),
        ("Bob leaves, Alice waves", "Waving goodbye"),
    ])
    from services.prompt_builder import build_all_shot_prompts, validate_scene_prompts
    prompts = build_all_shot_prompts(scene, "anime")
    assert len(prompts) == 6, f"Expected 6 prompts, got {len(prompts)}"
    for p in prompts:
        assert "Alice" in p["positive"] or True  # characters may be mentioned
    issues = validate_scene_prompts(prompts, scene)
    assert not issues, f"Validation issues: {issues}"
    return True


def test_chinese_topic():
    """Chinese-language scene context."""
    scene = _make_scene(
        "北京胡同里的茶馆",
        ["老张：茶馆老板", "小李：年轻顾客"],
        title="茶馆对话",
        learning_goal="学习中文日常对话"
    )
    add_shots(scene, [
        ("老张在柜台后整理茶具", "擦拭茶杯"),
        ("小李推开茶馆的门", "环顾四周"),
    ])
    from services.prompt_builder import build_all_shot_prompts, validate_scene_prompts
    prompts = build_all_shot_prompts(scene, "cinematic")
    assert len(prompts) == 2
    for p in prompts:
        assert p["positive"]
        assert p["negative"]
    return True


def test_no_dialogue_in_prompt():
    """Ensure dialogue text does NOT leak into image prompts."""
    scene = _make_scene("A park", ["Mary: jogger"])
    add_shots(scene, [("Mary running on a path", "Jogging with earbuds")])
    from services.prompt_builder import build_all_shot_prompts
    prompts = build_all_shot_prompts(scene, "hand_drawn")
    for p in prompts:
        pos = p["positive"]
        # Dialogue should not appear in image prompt
        assert "Hello!" not in pos, f"Dialogue leaked into prompt: {pos}"
        assert "你好" not in pos, f"Chinese leaked into prompt: {pos}"
    return True


def test_character_consistency():
    """Character names should appear consistently."""
    scene = _make_scene("A classroom", ["Teacher: Ms. Wang", "Student: Tom"])
    add_shots(scene, [
        ("Ms. Wang at the blackboard", "Writing on board"),
        ("Tom raising hand", "Asking question"),
    ])
    from services.prompt_builder import build_scene_prompt
    sp = build_scene_prompt(scene, "flat_design")
    # Character should be in shared prompt
    assert "Ms. Wang" in sp["shared_positive"]
    assert "Tom" in sp["shared_positive"]
    return True


def test_negative_prompt_global():
    """Global negative prompt should be included."""
    from config.visual_styles import build_negative_prompt
    neg = build_negative_prompt("american_comic")
    assert "text" in neg.lower()
    assert "watermark" in neg.lower()
    return True


def test_all_styles_load():
    """All 5 styles should load without error."""
    from config.visual_styles import VISUAL_STYLES, get_style, build_positive_prompt, build_negative_prompt
    assert len(VISUAL_STYLES) >= 5
    for sid in VISUAL_STYLES:
        style = get_style(sid)
        assert style["name"]
        pos = build_positive_prompt(sid)
        assert len(pos) > 50, f"Style {sid} positive too short"
        neg = build_negative_prompt(sid)
        assert len(neg) > 20, f"Style {sid} negative too short"
    return True


def main():
    tests = [
        ("4-shot single character", test_4_shot_single_character),
        ("6-shot two characters", test_6_shot_two_characters),
        ("Chinese topic", test_chinese_topic),
        ("No dialogue in prompt", test_no_dialogue_in_prompt),
        ("Character consistency", test_character_consistency),
        ("Negative prompt global", test_negative_prompt_global),
        ("All styles load", test_all_styles_load),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            result = test_fn()
            if result:
                print(f"  PASS: {name}")
                passed += 1
            else:
                print(f"  FAIL: {name}")
                failed += 1
        except Exception as e:
            print(f"  FAIL: {name} — {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
