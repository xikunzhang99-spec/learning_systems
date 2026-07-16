import streamlit as st
from services.code_explain_service import explain_code_stream
from services.record_service import (
    save_code_record,
    list_code_records,
    get_code_record,
    delete_code_record,
    get_distinct_languages,
)
from utils.language_detect import detect_language


LANGUAGES = ["自动识别", "Python", "JavaScript", "Shell", "SQL", "HTML", "CSS", "其他"]
EXPLAIN_LEVELS = ["简单解释", "详细解释", "教学式解释"]


def show():
    st.title("💻 代码解释")
    st.markdown("输入代码，AI 将一步步帮你理解每个细节。")

    # ---- 输入区域 ----
    code = st.text_area(
        "请输入代码",
        height=220,
        placeholder="粘贴一行或多行代码到这里...",
        key="code_input",
    )

    lang_col, level_col = st.columns(2)
    with lang_col:
        language_choice = st.selectbox("代码语言", LANGUAGES, key="language")
    with level_col:
        explain_level = st.selectbox("解释深度", EXPLAIN_LEVELS, key="explain_level")

    # 语言解析
    if language_choice == "自动识别" and code.strip():
        resolved_language = detect_language(code)
    elif language_choice == "自动识别":
        resolved_language = "其他"
    else:
        resolved_language = language_choice

    if language_choice == "自动识别" and code.strip():
        st.caption(f"自动识别语言：**{resolved_language}**")

    explain_clicked = st.button("开始解释代码", type="primary", use_container_width=True)

    # ---- 流式结果 ----
    if explain_clicked and not code.strip():
        st.warning("请先输入代码。")
    elif explain_clicked and code.strip():
        with st.spinner("AI 正在分析代码..."):
            stream = explain_code_stream(code, resolved_language, explain_level)

        st.markdown("---")
        st.markdown("### AI 解释结果")

        full_response = st.write_stream(stream)

        st.success("解释完成！")

        # 流式完成后保存到数据库
        try:
            summary = _extract_summary(full_response, code)
            record_id = save_code_record(
                code_text=code,
                language=resolved_language,
                explain_level=explain_level,
                ai_response=full_response,
                summary=summary,
            )
            st.session_state["last_record_id"] = record_id
            st.info(f"已自动保存到学习记录（ID: {record_id}）")
        except Exception as e:
            st.warning(f"保存记录失败：{e}")

    # ---- 学习记录 ----
    st.markdown("---")
    st.markdown("### 📝 学习记录")
    st.markdown("查看和搜索历史代码解释记录。")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        keyword = st.text_input("关键词搜索", placeholder="搜索代码或摘要...", key="record_search")
    with col2:
        languages = get_distinct_languages()
        language_filter = st.selectbox("按语言筛选", ["全部"] + languages, key="record_lang_filter")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("搜索", use_container_width=True, key="record_search_btn")

    lang = None if language_filter == "全部" else language_filter
    kw = keyword if keyword.strip() else None
    records = list_code_records(keyword=kw, language=lang)

    if not records:
        st.info("暂无学习记录，先解释一段代码吧。")
    else:
        st.markdown(f"共找到 **{len(records)}** 条记录")

        for rec in records:
            summary_text = rec.get("summary", "无摘要") or "无摘要"
            with st.expander(
                f"#{rec['id']} · {rec.get('language', '未知')} · {summary_text[:80]} · {rec.get('created_at', '')}"
            ):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    detail = get_code_record(rec["id"])
                    if detail:
                        st.markdown("**原始代码**")
                        lang_name = (detail.get("language") or "").lower()
                        st.code(detail["code_text"], language=lang_name if lang_name else None)
                        st.markdown("**解释深度**：" + (detail.get("explain_level") or ""))
                        st.markdown("**AI 解释**")
                        st.markdown(detail.get("ai_response") or "")
                with col_b:
                    if st.button("删除", key=f"del_{rec['id']}"):
                        delete_code_record(rec["id"])
                        st.rerun()


def _extract_summary(text: str, code: str) -> str:
    lines = text.strip().split("\n")
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


if __name__ == "__main__":
    show()
