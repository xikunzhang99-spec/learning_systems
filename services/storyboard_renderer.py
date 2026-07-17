import streamlit as st

TEMPLATES = {
    "grid4": {"cols": 2, "name": "2x2 Grid", "max_shots": 4},
    "grid6": {"cols": 3, "name": "3x2 Grid", "max_shots": 6},
    "horizontal_strip": {"cols": 0, "name": "Horizontal Strip", "max_shots": 6},
    "vertical_list": {"cols": 1, "name": "Vertical List", "max_shots": 6},
}


def get_template_options():
    return list(TEMPLATES.keys())


def get_template_name(template_id):
    return TEMPLATES.get(template_id, {}).get("name", template_id)


def render_storyboard_grid(scene, template="grid4", on_shot_click=None):
    """Render scene shots in a storyboard grid layout.

    Args:
        scene: dict with 'shots' list and metadata
        template: one of 'grid4', 'grid6', 'horizontal_strip', 'vertical_list'
        on_shot_click: optional callback(shot) when a shot card is clicked
    """
    shots = scene.get("shots", [])
    if not shots:
        st.info("No shots to display.")
        return

    tpl = TEMPLATES.get(template, TEMPLATES["vertical_list"])

    if template == "horizontal_strip":
        cols = st.columns(len(shots))
        for i, shot in enumerate(shots):
            with cols[i]:
                _render_shot_card(shot, i, len(shots))
    elif template in ("grid4", "grid6"):
        cols_per_row = tpl["cols"]
        for row_start in range(0, len(shots), cols_per_row):
            row_shots = shots[row_start : row_start + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, shot in enumerate(row_shots):
                with cols[j]:
                    _render_shot_card(shot, row_start + j, len(shots))
    else:
        for i, shot in enumerate(shots):
            _render_shot_card(shot, i, len(shots))


def _render_shot_card(shot, index, total):
    order = shot.get("order", index + 1)
    dialogue = shot.get("dialogue", "")
    dialogue_zh = shot.get("dialogue_zh", "")
    narration = shot.get("narration", "")
    visual = shot.get("visual_description", "")
    action = shot.get("character_action", "")

    with st.container(border=True):
        st.caption(f"Shot {order}/{total}")

        # Image
        image_path = shot.get("image_path", "")
        if image_path and __import__("os").path.isfile(image_path):
            st.image(image_path, use_container_width=True)

        # Script section
        has_script = dialogue or dialogue_zh or narration
        if has_script:
            with st.container(border=True):
                st.caption("Script")
                if narration:
                    st.markdown(f"*{narration}*")
                if dialogue:
                    st.markdown(f"**EN:** {dialogue}")
                if dialogue_zh:
                    st.markdown(f"**ZH:** {dialogue_zh}")

        if visual or action:
            with st.expander("Image Prompt (visual description)"):
                if visual:
                    st.markdown(f"*{visual}*")
                if action:
                    st.markdown(f"🎬 {action}")

        # Bound learning items
        bound_ids = shot.get("bound_items", [])
        if bound_ids:
            with st.expander(f"Learning Items ({len(bound_ids)})"):
                from services.item_service import get_item
                for bid in bound_ids:
                    item = get_item(bid)
                    if item:
                        st.markdown(
                            f"**{item['english']}** — {item['chinese']} "
                            f"`{item['item_type']}`"
                        )


def render_shot_detail(shot, items_detail=None):
    """Render a full-detail view of a single shot for the learning mode."""
    order = shot.get("order", "?")
    st.subheader(f"Shot {order}")

    visual = shot.get("visual_description", "")
    if visual:
        st.markdown(f"*{visual}*")

    st.markdown("### Dialogue")
    dialogue = shot.get("dialogue", "")
    st.markdown(f"**{dialogue}**")
    dialogue_zh = shot.get("dialogue_zh", "")
    if dialogue_zh:
        st.caption(dialogue_zh)

    action = shot.get("character_action", "")
    if action:
        st.markdown(f"*{action}*")

    bound_ids = shot.get("bound_items", [])
    if bound_ids:
        st.markdown("### Learning Items")
        from services.item_service import get_item
        for bid in bound_ids:
            item = get_item(bid)
            if item:
                _render_item_card(item)


def _render_item_card(item, review_mode=None):
    """Render a single learning item card.
    review_mode: None ('learning'), 'hide_chinese', 'hide_english', 'image_recall'
    """
    item_id = item["id"]
    english = item.get("english", "")
    chinese = item.get("chinese", "")
    item_type = item.get("item_type", "word")
    notes = item.get("notes", "")
    mastery = item.get("mastery_level", 0)

    reveal_key = f"reveal_{item_id}_{review_mode or 'learn'}"

    with st.container(border=True):
        type_badge = {"word": "W", "phrase": "P", "expression": "E", "sentence": "S"}.get(
            item_type, "?"
        )
        st.caption(f"[{type_badge}] Mastery: {'★' * mastery}{'☆' * (3 - mastery)}")

        if review_mode == "hide_chinese":
            st.markdown(f"**{english}**")
            if st.button("Reveal", key=f"btn_{reveal_key}"):
                st.session_state[reveal_key] = True
            if st.session_state.get(reveal_key):
                st.markdown(f"*{chinese}*")
                if notes:
                    st.caption(notes)
                _review_rating_buttons(item_id)
        elif review_mode == "hide_english":
            st.markdown(f"**{chinese}**")
            if st.button("Reveal", key=f"btn_{reveal_key}"):
                st.session_state[reveal_key] = True
            if st.session_state.get(reveal_key):
                st.markdown(f"*{english}*")
                if notes:
                    st.caption(notes)
                _review_rating_buttons(item_id)
        elif review_mode == "image_recall":
            if st.button("What is this?", key=f"btn_{reveal_key}"):
                st.session_state[reveal_key] = True
            if st.session_state.get(reveal_key):
                st.markdown(f"**{english}** — *{chinese}*")
                _review_rating_buttons(item_id)
        else:
            st.markdown(f"**{english}** — *{chinese}*")
            if notes:
                st.caption(notes)


def _review_rating_buttons(item_id):
    from services.item_service import get_item, update_mastery
    item = get_item(item_id)
    current = item["mastery_level"] if item else 0

    c1, c2 = st.columns(2)
    with c1:
        if st.button("I knew it", key=f"knew_{item_id}"):
            update_mastery(item_id, min(3, current + 1))
            st.rerun()
    with c2:
        if st.button("Need practice", key=f"need_{item_id}"):
            update_mastery(item_id, max(0, current - 1))
            st.rerun()
