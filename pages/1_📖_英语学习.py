import streamlit as st
from services.topic_service import (
    create_topic, update_topic, delete_topic, get_topic, list_topics,
    get_topic_stats, get_all_tags,
)
from services.item_service import (
    create_item, create_items_batch, update_item, delete_item,
    get_item, list_items, update_mastery, get_item_counts_by_topic,
)
from services.scene_service import (
    generate_scene_script, generate_scene_script_stream, get_scene,
    list_scenes, delete_scene, update_shot, reorder_shots,
    delete_shot, add_shot, regenerate_shot, regenerate_scene,
    update_scene_status, get_scene_items_detail,
)
from services.storyboard_renderer import (
    render_storyboard_grid, render_shot_detail, get_template_options,
    get_template_name,
)


def show():
    st.title("📖 英语学习")

    # Initialize session state
    if "en_nav" not in st.session_state:
        st.session_state.en_nav = "home"
    if "selected_topic_id" not in st.session_state:
        st.session_state.selected_topic_id = None
    if "selected_scene_id" not in st.session_state:
        st.session_state.selected_scene_id = None

    if st.session_state.en_nav == "home":
        _show_home()
    elif st.session_state.en_nav == "topic_detail":
        _show_topic_detail()
    elif st.session_state.en_nav == "scene_gen":
        _show_scene_generation()
    elif st.session_state.en_nav == "scene_review":
        _show_scene_review()


# ── Home ────────────────────────────────────────────────────────────────

def _show_home():
    st.header("Expression Library")

    # Create Topic
    st.subheader("+ New Topic")
    title = st.text_input("Title", key="new_topic_title",
                           placeholder="e.g., Daily Office English")
    col1, col2 = st.columns(2)
    with col1:
        description = st.text_area("Description", key="new_topic_desc",
                                    placeholder="What is this topic about?")
    with col2:
        tags = st.text_input("Tags (comma separated)", key="new_topic_tags",
                              placeholder="work, office, meeting")
    if st.button("Create Topic", type="primary", key="btn_create_topic"):
        if title.strip():
            create_topic(title.strip(), description.strip(), tags.strip())
            st.success(f"Topic '{title}' created!")
            st.rerun()
        else:
            st.error("Title is required.")

    # Search / Filter
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("Search", key="home_search", placeholder="Search by keyword...")
    with col2:
        all_tags = get_all_tags()
        tag_filter = st.selectbox("Tag", ["All"] + all_tags, key="home_tag_filter")
    with col3:
        status_filter = st.selectbox("Status", ["active", "archived", "all"], key="home_status")

    st.divider()

    # Topic List
    status_arg = None if status_filter == "all" else status_filter
    tag_arg = None if tag_filter == "All" else tag_filter
    topics = list_topics(keyword=keyword or None, tag=tag_arg, status=status_arg)

    if not topics:
        st.info("No topics yet. Create your first topic above!")
        return

    for topic in topics:
        stats = get_topic_stats(topic["id"])
        tags_list = [t.strip() for t in topic.get("tags", "").split(",") if t.strip()]

        with st.container(border=True):
            col1, col2 = st.columns([4, 1.5])
            with col1:
                st.markdown(f"### {topic['title']}")
                st.caption(
                    f"{topic.get('date', '')}  |  "
                    f"Items: {stats['item_count']}  |  "
                    f"Scenes: {stats['scene_count']}"
                )
                if topic.get("description"):
                    st.markdown(topic["description"][:200])
                if tags_list:
                    st.markdown(" ".join(f"`{t}`" for t in tags_list))
            with col2:
                if st.button("Open", key=f"open_topic_{topic['id']}", use_container_width=True):
                    st.session_state.selected_topic_id = topic["id"]
                    st.session_state.en_nav = "topic_detail"
                    st.rerun()
                if st.button("Delete", key=f"del_topic_{topic['id']}", use_container_width=True):
                    st.session_state[f"confirm_delete_{topic['id']}"] = True
                    st.rerun()

            if st.session_state.get(f"confirm_delete_{topic['id']}"):
                st.warning(f"Delete topic '{topic['title']}'? This will also delete all items and scenes inside it.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes, delete", key=f"yes_del_{topic['id']}"):
                        delete_topic(topic["id"])
                        st.session_state.pop(f"confirm_delete_{topic['id']}", None)
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel_del_{topic['id']}"):
                        st.session_state.pop(f"confirm_delete_{topic['id']}", None)
                        st.rerun()


# ── Topic Detail ─────────────────────────────────────────────────────────

def _show_topic_detail():
    topic_id = st.session_state.selected_topic_id
    topic = get_topic(topic_id)

    if not topic:
        st.error("Topic not found.")
        if st.button("Back to Home"):
            st.session_state.en_nav = "home"
            st.rerun()
        return

    st.header(topic["title"])
    st.caption(f"{topic.get('date', '')}  |  {topic.get('description', '')}")

    if st.button("Back to Home", key="btn_back_home"):
        st.session_state.en_nav = "home"
        st.session_state.selected_topic_id = None
        st.rerun()

    st.divider()

    # Item counts
    counts = get_item_counts_by_topic(topic_id)
    total = sum(counts.values())
    st.caption(
        f"Total: {total}  |  Word: {counts['word']}  |  Phrase: {counts['phrase']}  "
        f"|  Expression: {counts['expression']}  |  Sentence: {counts['sentence']}"
    )

    # Smart Query
    # Smart Query
    st.subheader("🔍 Smart Query (AI-powered lookup)")
    query_text = st.text_input(
        "Enter English or Chinese",
        key="smart_query_input",
        placeholder="e.g., accumulate / 积累经验 / AI can interact with the physical world",
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Query", key="btn_smart_query", use_container_width=True):
            if query_text.strip():
                with st.spinner("Looking up..."):
                    try:
                        from services.lookup_service import lookup_expression
                        result = lookup_expression(query_text.strip())
                        st.session_state.smart_query_result = result
                        st.rerun()
                    except Exception as e:
                        st.error(f"Query failed: {e}")
                        st.session_state.smart_query_result = None
            else:
                st.warning("Please enter some text.")
    with c2:
        if st.session_state.get("smart_query_result"):
            if st.button("Clear Result", key="btn_clear_sq", use_container_width=True):
                st.session_state.smart_query_result = None
                st.rerun()

    if st.session_state.get("smart_query_result"):
        result = st.session_state.smart_query_result
        st.success(f"Found: {result.get('english', '')}")

        with st.form(key="smart_query_save_form"):
            col1, col2 = st.columns(2)
            with col1:
                english = st.text_input("English", value=result.get("english", ""),
                                         key="sq_english")
                item_type = st.selectbox(
                    "Type", ["word", "phrase", "expression", "sentence"],
                    index=["word", "phrase", "expression", "sentence"].index(
                        result.get("item_type", "word")
                    ),
                    key="sq_type",
                )
                notes = st.text_area("Notes", value=result.get("notes", ""), key="sq_notes")
            with col2:
                chinese = st.text_input("Chinese", value=result.get("chinese", ""),
                                         key="sq_chinese")
                example_en = st.text_area(
                    "Example (EN)", value=result.get("example_en", ""), key="sq_example_en"
                )
                example_zh = st.text_input(
                    "Example (ZH)", value=result.get("example_zh", ""), key="sq_example_zh"
                )
            related = st.text_input(
                "Related Words", value=result.get("related_words", ""), key="sq_related"
            )
            st.caption(f"Confidence: {result.get('confidence', '?')}")

            submitted = st.form_submit_button("Save to This Topic", type="primary")
            if submitted and english.strip() and chinese.strip():
                create_item(
                    topic_id, english.strip(), chinese.strip(),
                    item_type=item_type, notes=notes.strip(),
                    original_text=query_text.strip(),
                )
                st.session_state.smart_query_result = None
                st.success("Saved!")
                st.rerun()

    # Batch query
    st.markdown("**Batch Query** (one per line)")
    batch_text = st.text_area(
        "Input",
        key="sq_batch_input",
        placeholder="accumulate\n积累经验\nAI can interact with the physical world",
        height=80,
    )
    if st.button("Batch Lookup", key="btn_sq_batch") and batch_text.strip():
        lines = [l.strip() for l in batch_text.split("\n") if l.strip()]
        st.session_state.sq_batch_results = []
        progress = st.progress(0)
        for i, line in enumerate(lines):
            try:
                from services.lookup_service import lookup_expression
                r = lookup_expression(line)
                st.session_state.sq_batch_results.append({"input": line, "result": r})
            except Exception as e:
                st.session_state.sq_batch_results.append(
                    {"input": line, "error": str(e)}
                )
            progress.progress((i + 1) / len(lines))
        progress.empty()

    if st.session_state.get("sq_batch_results"):
        st.markdown(f"**Results ({len(st.session_state.sq_batch_results)})**")
        save_all = st.button("Save All to Topic", type="primary", key="btn_sq_save_all")
        for i, item in enumerate(st.session_state.sq_batch_results):
            if item.get("error"):
                st.error(f"{item['input']}: {item['error']}")
            else:
                r = item["result"]
                cols = st.columns([0.5, 2, 2, 1, 1])
                with cols[0]:
                    st.caption(f"#{i+1}")
                with cols[1]:
                    st.markdown(f"**{r.get('english', '?')}**")
                with cols[2]:
                    st.caption(r.get("chinese", ""))
                with cols[3]:
                    st.caption(f"`{r.get('item_type', '?')}`")
                with cols[4]:
                    if save_all:
                        try:
                            create_item(
                                topic_id,
                                r.get("english", item["input"]),
                                r.get("chinese", ""),
                                item_type=r.get("item_type", "word"),
                                notes=r.get("notes", ""),
                                original_text=item["input"],
                            )
                            st.success("✓")
                        except Exception:
                            st.caption("Skip")
        if save_all:
            st.session_state.sq_batch_results = []
            st.rerun()

    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        type_filter = st.selectbox(
            "Type", ["All", "word", "phrase", "expression", "sentence"], key="item_type_filter"
        )
    with c2:
        mastery_filter = st.selectbox(
            "Mastery", ["All", "0 - New", "1 - Learning", "2 - Familiar", "3 - Mastered"],
            key="item_mastery_filter"
        )
    with c3:
        item_search = st.text_input("Search items", key="item_search_input")

    item_type_arg = None if type_filter == "All" else type_filter
    mastery_arg = None if mastery_filter == "All" else int(mastery_filter[0])
    items = list_items(
        topic_id=topic_id,
        item_type=item_type_arg,
        mastery_level=mastery_arg,
        keyword=item_search or None,
    )

    st.divider()

    # Item selector for scene generation
    if "item_selection" not in st.session_state:
        st.session_state.item_selection = set()

    # Quick filters
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Select All", use_container_width=True, key="sel_all"):
            st.session_state.item_selection = {it["id"] for it in items}
            st.rerun()
    with c2:
        if st.button("Deselect All", use_container_width=True, key="desel_all"):
            st.session_state.item_selection = set()
            st.rerun()
    with c3:
        if st.button("Select Unmastered", use_container_width=True, key="sel_unmastered"):
            st.session_state.item_selection = {
                it["id"] for it in items if it.get("mastery_level", 0) < 3
            }
            st.rerun()
    with c4:
        sel_type = st.selectbox(
            "By type", ["All", "word", "phrase", "expression", "sentence"],
            key="sel_type_filter", label_visibility="collapsed",
        )
        if st.button("Select Type", use_container_width=True, key="sel_by_type"):
            if sel_type == "All":
                st.session_state.item_selection = {it["id"] for it in items}
            else:
                st.session_state.item_selection = {
                    it["id"] for it in items if it.get("item_type") == sel_type
                }
            st.rerun()

    selected_count = len(st.session_state.item_selection)
    if selected_count > 0:
        st.info(f"{selected_count} of {len(items)} items selected")

    # Generate Scene button
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Generate Scene", type="primary", use_container_width=True,
                      disabled=selected_count == 0, key="btn_gen_scene"):
            st.session_state.en_nav = "scene_gen"
            st.rerun()
    with c2:
        if not st.session_state.item_selection:
            st.caption("Select items above to enable scene generation.")

    # Item list + add/edit form
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Items")
        if not items:
            st.info("No items yet. Add some on the right.")
        else:
            for item in items:
                item_id = item["id"]
                is_selected = item_id in st.session_state.item_selection

                with st.container(border=True):
                    c1, c2, c3 = st.columns([0.5, 3, 0.5])
                    with c1:
                        checked = st.checkbox(
                            "Select", value=is_selected, key=f"chk_{item_id}",
                            label_visibility="collapsed",
                        )
                        if checked != is_selected:
                            if checked:
                                st.session_state.item_selection.add(item_id)
                            else:
                                st.session_state.item_selection.discard(item_id)
                            st.rerun()
                    with c2:
                        type_badge = {"word": "W", "phrase": "P", "expression": "E", "sentence": "S"}
                        st.markdown(
                            f"**{item['english']}** — {item['chinese']} "
                            f"`{type_badge.get(item['item_type'], '?')}`"
                        )
                        mastery = item.get("mastery_level", 0)
                        st.caption(f"Mastery: {'★' * mastery}{'☆' * (3 - mastery)}")
                        if item.get("notes"):
                            st.caption(item["notes"][:100])
                    with c3:
                        if st.button("Edit", key=f"edit_item_{item_id}"):
                            st.session_state.edit_item_id = item_id
                            st.rerun()
                        if st.button("Del", key=f"del_item_{item_id}"):
                            delete_item(item_id)
                            st.session_state.item_selection.discard(item_id)
                            st.rerun()

    with col_right:
        edit_item_id = st.session_state.get("edit_item_id")
        if edit_item_id:
            st.subheader("Edit Item")
            edit_item = get_item(edit_item_id)
            if edit_item:
                _item_form(topic_id, item=edit_item, is_edit=True)
            if st.button("Cancel Edit"):
                st.session_state.pop("edit_item_id", None)
                st.rerun()
        else:
            _item_form(topic_id)

    # Scenes for this topic
    st.divider()
    st.subheader("Scenes")
    scenes = list_scenes(topic_id=topic_id)
    if not scenes:
        st.info("No scenes generated yet. Select items and click 'Generate Scene' above.")
    else:
        for scene in scenes:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{scene['title']}**")
                    st.caption(
                        f"Status: {scene.get('status', 'draft')}  |  "
                        f"{scene.get('created_at', '')[:16]}"
                    )
                with c2:
                    if st.button("Open", key=f"open_scene_{scene['id']}", use_container_width=True):
                        st.session_state.selected_scene_id = scene["id"]
                        st.session_state.en_nav = "scene_review"
                        st.rerun()
                with c3:
                    if st.button("Del", key=f"del_scene_{scene['id']}"):
                        delete_scene(scene["id"])
                        st.rerun()


def _item_form(topic_id, item=None, is_edit=False):
    """Form for adding or editing a learning item."""
    prefix = "edit_" if is_edit else "new_"
    default = item or {}

    with st.form(key=f"{prefix}item_form"):
        english = st.text_input("English", value=default.get("english", ""),
                                 key=f"{prefix}eng", placeholder="e.g., touch base")
        chinese = st.text_input("Chinese", value=default.get("chinese", ""),
                                 key=f"{prefix}chn", placeholder="e.g., 联系一下")
        item_type = st.selectbox(
            "Type", ["word", "phrase", "expression", "sentence"],
            index=["word", "phrase", "expression", "sentence"].index(
                default.get("item_type", "word")
            ),
            key=f"{prefix}type",
        )
        notes = st.text_area("Notes (optional)", value=default.get("notes", ""),
                              key=f"{prefix}notes", placeholder="Usage context, example...")
        original_text = st.text_area("Original Text (optional)",
                                      value=default.get("original_text", ""),
                                      key=f"{prefix}orig",
                                      placeholder="Original sentence/phrase from source")
        corrected_text = st.text_area("Corrected Text (optional)",
                                       value=default.get("corrected_text", ""),
                                       key=f"{prefix}corr",
                                       placeholder="Teacher's correction if any")

        submitted = st.form_submit_button(
            "Save Changes" if is_edit else "Add Item", type="primary"
        )

        if submitted:
            if not english.strip() or not chinese.strip():
                st.error("English and Chinese are required.")
            else:
                if is_edit:
                    update_item(
                        item["id"],
                        english=english.strip(),
                        chinese=chinese.strip(),
                        item_type=item_type,
                        notes=notes.strip(),
                        original_text=original_text.strip(),
                        corrected_text=corrected_text.strip(),
                    )
                    st.success("Item updated!")
                    st.session_state.pop("edit_item_id", None)
                else:
                    create_item(
                        topic_id, english.strip(), chinese.strip(),
                        item_type=item_type, notes=notes.strip(),
                        original_text=original_text.strip(),
                        corrected_text=corrected_text.strip(),
                    )
                    st.success("Item added!")
                st.rerun()

    # Batch input
    if not is_edit:
        with st.expander("Batch Input"):
            st.caption("One per line: english | chinese | type")
            batch_text = st.text_area(
                "Batch", key="batch_input",
                placeholder="touch base | 联系一下 | phrase\ndeadline | 截止日期 | word",
                height=120,
            )
            if st.button("Import Batch"):
                lines = [l.strip() for l in batch_text.split("\n") if l.strip()]
                batch_items = []
                for line in lines:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2:
                        batch_items.append({
                            "topic_id": topic_id,
                            "english": parts[0],
                            "chinese": parts[1],
                            "item_type": parts[2] if len(parts) > 2 else "word",
                        })
                if batch_items:
                    count = create_items_batch(batch_items)
                    st.success(f"Imported {count} items!")
                    st.rerun()


# ── Scene Generation ─────────────────────────────────────────────────────

def _show_scene_generation():
    topic_id = st.session_state.selected_topic_id
    topic = get_topic(topic_id)

    if not topic:
        st.error("Topic not found.")
        return

    st.header(f"Scene Generation: {topic['title']}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back to Topic", key="btn_back_topic"):
            st.session_state.en_nav = "topic_detail"
            st.rerun()
    with c2:
        if st.button("Back to Home", key="btn_gen_home"):
            st.session_state.en_nav = "home"
            st.rerun()

    st.divider()

    selected_ids = list(st.session_state.get("item_selection", set()))
    selected_items = [get_item(iid) for iid in selected_ids]
    selected_items = [it for it in selected_items if it is not None]

    if not selected_items:
        st.warning("No items selected. Go back to the topic and select items first.")
        return

    st.markdown(f"**Selected Items**: {len(selected_items)}")
    for it in selected_items:
        st.caption(f"• {it['english']} — {it['chinese']} `{it['item_type']}`")

    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        visual_style = st.text_input(
            "Visual Style", value="modern illustration, clean and colorful",
            key="gen_style", placeholder="e.g., cinematic, watercolor, cartoon"
        )
    with c2:
        shot_count = st.slider("Shot Count", 4, 6, 5, key="gen_shot_count")
    with c3:
        template_choice = st.selectbox(
            "Template", get_template_options(),
            format_func=get_template_name, key="gen_template"
        )

    # Store template choice
    if "scene_template" not in st.session_state:
        st.session_state.scene_template = "grid4"

    if st.button("Generate Scene Script", type="primary", use_container_width=True,
                  key="btn_gen"):
        st.session_state.scene_template = template_choice

        log_container = st.empty()
        status_container = st.status("Generating scene script...", expanded=True)

        for status_line in generate_scene_script_stream(
            topic_id, selected_ids, visual_style, shot_count
        ):
            status_container.update(label=status_line[:120])

            if status_line.startswith("Done|scene_id="):
                scene_id = int(status_line.split("=")[1])
                st.session_state.selected_scene_id = scene_id
                status_container.update(
                    label="Generation complete!", state="complete"
                )
                st.success("Scene script generated!")
                st.rerun()

    st.divider()

    # Show existing generated scenes for this topic
    scenes = list_scenes(topic_id=topic_id)
    if scenes:
        st.subheader("Generated Scenes")
        for scene in scenes:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{scene['title']}**")
                    st.caption(
                        f"Status: {scene.get('status', 'draft')}  |  "
                        f"Shots: {_count_shots(scene['id'])}  |  "
                        f"{scene.get('created_at', '')[:16]}"
                    )
                with c2:
                    if st.button("Preview/Edit", key=f"edit_scene_{scene['id']}",
                                 use_container_width=True):
                        st.session_state.selected_scene_id = scene["id"]
                        st.rerun()
                with c3:
                    if st.button("Del", key=f"del_gscene_{scene['id']}"):
                        delete_scene(scene["id"])
                        st.rerun()

    # Scene preview/editor for selected scene
    selected_scene_id = st.session_state.get("selected_scene_id")
    if selected_scene_id:
        st.divider()
        st.subheader("Scene Script Editor")

        scene = get_scene(selected_scene_id)
        if scene:
            _render_scene_editor(scene, topic_id)


def _render_scene_editor(scene, topic_id):
    scene_id = scene["id"]

    # Scene metadata
    with st.expander("Scene Info", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Title", value=scene.get("title", ""), key=f"scene_title_{scene_id}")
            st.text_area("Background", value=scene.get("background", ""), key=f"scene_bg_{scene_id}")
        with c2:
            st.text_area("Learning Goal", value=scene.get("learning_goal", ""),
                          key=f"scene_goal_{scene_id}")
            st.caption(f"Status: {scene.get('status', 'draft')}")
            st.caption(f"Template: {scene.get('template', 'grid4')}")
            st.caption(f"Model: {scene.get('model', '')}")

    # Shot list
    shots = scene.get("shots", [])
    st.markdown(f"### Shots ({len(shots)})")

    for i, shot in enumerate(shots):
        shot_id = shot["id"]
        with st.expander(
            f"Shot {shot.get('order', i+1)}: {shot.get('dialogue', '')[:60]}...",
            expanded=i < 2,
        ):
            c1, c2 = st.columns([3, 1])
            with c1:
                new_order = st.number_input(
                    "Order", value=shot.get("order", i + 1),
                    min_value=1, max_value=len(shots),
                    key=f"shot_order_{shot_id}"
                )
                if new_order != shot.get("order"):
                    update_shot(shot_id, order=new_order)
                    st.rerun()

                new_dialogue = st.text_area(
                    "Dialogue", value=shot.get("dialogue", ""),
                    key=f"shot_dialogue_{shot_id}", height=68,
                )
                new_dialogue_zh = st.text_area(
                    "Dialogue (中文)", value=shot.get("dialogue_zh", ""),
                    key=f"shot_dialogue_zh_{shot_id}", height=68,
                )
                new_visual = st.text_area(
                    "Visual Description", value=shot.get("visual_description", ""),
                    key=f"shot_visual_{shot_id}", height=68,
                )
                new_action = st.text_area(
                    "Character Action", value=shot.get("character_action", ""),
                    key=f"shot_action_{shot_id}", height=68,
                )

            with c2:
                if st.button("Save Shot", key=f"save_shot_{shot_id}",
                             use_container_width=True):
                    update_shot(
                        shot_id,
                        dialogue=new_dialogue,
                        dialogue_zh=new_dialogue_zh,
                        visual_description=new_visual,
                        character_action=new_action,
                    )
                    st.success("Shot saved!")
                    st.rerun()

                if st.button("Regenerate", key=f"regen_shot_{shot_id}",
                             use_container_width=True):
                    with st.spinner("Regenerating..."):
                        regenerate_shot(scene_id, shot_id)
                    st.success("Shot regenerated!")
                    st.rerun()

                if st.button("Delete Shot", key=f"del_shot_{shot_id}",
                             use_container_width=True):
                    delete_shot(shot_id)
                    st.rerun()

            # Move up/down
            c1, c2 = st.columns(2)
            with c1:
                if i > 0 and st.button("Move Up", key=f"up_{shot_id}",
                                        use_container_width=True):
                    new_order = [s["id"] for s in shots]
                    new_order[i], new_order[i - 1] = new_order[i - 1], new_order[i]
                    reorder_shots(scene_id, new_order)
                    st.rerun()
            with c2:
                if i < len(shots) - 1 and st.button("Move Down", key=f"down_{shot_id}",
                                                      use_container_width=True):
                    new_order = [s["id"] for s in shots]
                    new_order[i], new_order[i + 1] = new_order[i + 1], new_order[i]
                    reorder_shots(scene_id, new_order)
                    st.rerun()

    # Image Prompt Preview
    with st.expander("🖼 View Image Prompts & Scripts", expanded=False):
        from services.prompt_builder import build_all_shot_prompts, validate_prompt
        from config.visual_styles import get_style_choices, get_style_name
        style_id = st.selectbox(
            "Visual Style", [s[0] for s in get_style_choices()],
            format_func=get_style_name, key="prompt_preview_style"
        )
        try:
            prompts = build_all_shot_prompts(scene, style_id)
            shots = scene.get("shots", [])
            for i, (p, shot) in enumerate(zip(prompts, shots)):
                st.markdown(f"**Shot {p['shot_order']}**")

                # Image Prompt
                st.caption("Image Prompt")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("*Positive*")
                    st.code(p["positive"][:500], language=None)
                with col_b:
                    st.markdown("*Negative*")
                    st.code(p["negative"][:500], language=None)

                # Validation
                issues = validate_prompt(p)
                if issues:
                    for issue in issues:
                        st.warning(f"Validation: {issue}")

                # Script (separate from image prompt)
                st.caption("Script")
                script_col1, script_col2 = st.columns(2)
                with script_col1:
                    dialogue = shot.get("dialogue", "")
                    if dialogue:
                        st.markdown(f"**EN:** {dialogue}")
                    narration = shot.get("narration", "")
                    if narration:
                        st.markdown(f"*Narration: {narration}*")
                with script_col2:
                    dialogue_zh = shot.get("dialogue_zh", "")
                    if dialogue_zh:
                        st.markdown(f"**ZH:** {dialogue_zh}")

                st.divider()
        except Exception as e:
            st.warning(f"Prompt preview unavailable: {e}")

    # Global actions
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("+ Add Empty Shot", use_container_width=True, key="add_shot_btn"):
            add_shot(scene_id)
            st.rerun()
    with c2:
        if st.button("Regenerate All Shots", use_container_width=True,
                      key="regen_all_shots"):
            with st.spinner("Regenerating entire scene..."):
                regenerate_scene(scene_id)
            st.success("Scene regenerated!")
            st.rerun()
    with c3:
        if st.button("🎨 Generate Images", use_container_width=True,
                      key="gen_images_btn"):
            with st.spinner("Generating images for all shots..."):
                try:
                    from services.image_service import generate_scene_images
                    results = generate_scene_images(scene_id)
                    success = sum(1 for v in results.values() if v)
                    failed = len(results) - success
                except Exception as e:
                    st.error(f"Image generation failed: {e}")
                    st.stop()
            if success > 0:
                msg = f"Generated {success}/{len(results)} images"
                if failed > 0:
                    msg += f" ({failed} failed)"
                st.success(msg)
                st.rerun()
            else:
                st.error(
                    f"All {len(results)} shots failed. "
                    "Check IMAGE_PROVIDER / IMAGE_API_KEY / IMAGE_MODEL in .env "
                    "and review the console logs for details."
                )
    with c4:
        if st.button("Confirm → Go to Review", use_container_width=True,
                      type="primary", key="confirm_scene"):
            update_scene_status(scene_id, "confirmed")
            st.session_state.selected_scene_id = scene_id
            st.session_state.en_nav = "scene_review"
            st.rerun()


def _count_shots(scene_id):
    from database.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM scene_shots WHERE scene_id = ?", (scene_id,))
    count = cursor.fetchone()["c"]
    conn.close()
    return count


# ── Scene Review ──────────────────────────────────────────────────────────

def _show_scene_review():
    scene_id = st.session_state.get("selected_scene_id")

    if not scene_id:
        st.warning("No scene selected.")
        if st.button("Go to Home"):
            st.session_state.en_nav = "home"
            st.rerun()
        return

    scene = get_scene(scene_id)
    if not scene:
        st.error("Scene not found.")
        if st.button("Go to Home"):
            st.session_state.en_nav = "home"
            st.rerun()
        return

    st.header(scene.get("title", "Scene Review"))
    st.caption(f"Learning Goal: {scene.get('learning_goal', '')}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back to Generation", key="btn_rev_gen"):
            st.session_state.en_nav = "scene_gen"
            st.rerun()
    with c2:
        if st.button("Back to Topic", key="btn_rev_topic"):
            st.session_state.en_nav = "topic_detail"
            st.rerun()

    st.divider()

    # Template selector
    template = st.selectbox(
        "Layout", get_template_options(), format_func=get_template_name,
        index=list(get_template_options()).index(
            st.session_state.get("scene_template", "grid4")
        ),
        key="review_template",
    )

    # Scene background info
    with st.expander("Scene Background", expanded=False):
        st.markdown(f"**Background**: {scene.get('background', '')}")
        characters = scene.get("characters", [])
        if isinstance(characters, str):
            import json
            characters = json.loads(characters)
        if characters:
            st.markdown("**Characters**:")
            for char in characters:
                st.caption(f"• {char}")
        st.caption(f"Status: {scene.get('status', 'draft')}")
        st.caption(f"Model: {scene.get('model', '')}")
        st.caption(f"Visual Style: {scene.get('visual_style', '')}")

    st.divider()

    # Storyboard grid
    st.subheader("Storyboard")
    render_storyboard_grid(scene, template=template)

    st.divider()

    # Shot detail viewer
    shots = scene.get("shots", [])
    if "active_shot_idx" not in st.session_state:
        st.session_state.active_shot_idx = 0

    if shots:
        shot_labels = [f"Shot {s.get('order', i+1)}" for i, s in enumerate(shots)]
        active_idx = st.radio(
            "Select Shot", range(len(shots)),
            format_func=lambda i: shot_labels[i],
            horizontal=True,
            key="shot_selector",
        )
        st.session_state.active_shot_idx = active_idx
        active_shot = shots[active_idx]

        st.divider()
        st.subheader(f"Shot {active_shot.get('order', active_idx + 1)} Detail")

        # Show image if available
        image_path = active_shot.get("image_path", "")
        if image_path:
            import os
            if os.path.isfile(image_path):
                st.image(image_path, use_container_width=True)

        render_shot_detail(active_shot)

        # Navigation
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if active_idx > 0:
                if st.button("← Previous Shot", use_container_width=True):
                    st.session_state.active_shot_idx = active_idx - 1
                    st.rerun()
        with c3:
            if active_idx < len(shots) - 1:
                if st.button("Next Shot →", use_container_width=True):
                    st.session_state.active_shot_idx = active_idx + 1
                    st.rerun()

    st.divider()

    # All learning items
    st.subheader("Learning Items in This Scene")
    items_detail = get_scene_items_detail(scene_id)
    if not items_detail:
        st.info("No learning items linked to this scene.")
    else:
        for item in items_detail:
            with st.container(border=True):
                type_badge = {"word": "W", "phrase": "P", "expression": "E", "sentence": "S"}
                st.markdown(
                    f"**{item['english']}** — {item['chinese']} "
                    f"`{type_badge.get(item['item_type'], '?')}`"
                )
                mastery = item.get("mastery_level", 0)
                st.caption(f"Mastery: {'★' * mastery}{'☆' * (3 - mastery)}")
                if item.get("notes"):
                    st.caption(item["notes"])
                if item.get("original_text"):
                    st.caption(f"Source: {item['original_text']}")


if __name__ == "__main__":
    show()
