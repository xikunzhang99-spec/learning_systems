import streamlit as st
from services.ai_service import chat
from services.search_service import search_term
from services.obsidian_writer import (
    save_note,
    note_exists,
    list_notes,
    read_note,
    search_notes,
)
from services.term_db import insert_term, list_terms

SYSTEM_PROMPT = """你是一个专业的知识整理助手，擅长将复杂概念用通俗易懂的方式解释清楚。

你的任务是基于提供的搜索结果，为给定的术语或缩写生成一份结构化的知识笔记。

要求：
1. 所有内容用中文输出
2. 一句话解释要精炼，让完全不懂的人也能有个基本概念
3. 通俗理解用类比、比喻等手法，让读者产生直观感受
4. 专业定义要准确，但也要解释其中的关键术语
5. 使用场景列举 2-4 个真实世界的应用
6. 相关概念列出 3-5 个关联术语，并简要说明关联
7. 常见误区指出 1-2 个新手容易犯的理解偏差
8. 例子给出具体的、可感知的实例
9. 标签根据术语所属领域自动生成，格式为 #标签1 #标签2
10. 来源链接列出搜索结果中实际提供的 URL

请严格按照以下 Markdown 格式输出：

# {术语名称}

## 一句话解释
...

## 通俗理解
...

## 专业定义
...

## 使用场景
- ...
- ...

## 相关概念
- **概念A**：简要说明
- **概念B**：简要说明

## 常见误区
- 误区：... 正解：...
- 误区：... 正解：...

## 例子
...

## 来源链接
- [标题](URL)
- [标题](URL)

## 标签
#术语库 #领域标签 #更多标签"""


def _build_search_context(search_results: list) -> str:
    if not search_results:
        return "暂无搜索结果。"
    parts = []
    for i, r in enumerate(search_results, 1):
        parts.append(f"[来源{i}] 标题：{r.title}\n网址：{r.url}\n内容：{r.content}\n")
    return "\n---\n".join(parts)


def show():
    st.title("📡 专业术语解释")
    st.caption("输入术语 → 联网搜索 → AI 解释 → 一键保存到 Obsidian")

    tab1, tab2 = st.tabs(["🔍 搜索新术语", "📚 浏览术语库"])

    # ============================================
    # Tab 1: 搜索新术语
    # ============================================
    with tab1:
        if "term_explanation" not in st.session_state:
            st.session_state.term_explanation = ""
        if "term_last" not in st.session_state:
            st.session_state.term_last = ""
        if "term_sources" not in st.session_state:
            st.session_state.term_sources = []

        col1, col2 = st.columns([4, 1])
        with col1:
            term = st.text_input(
                "输入术语或缩写",
                placeholder="例如：RAG、Transformer、IDC、Kubernetes...",
                key="term_input",
            )
        with col2:
            st.write("")
            search_btn = st.button(
                "🔍 搜索并解释", type="primary", use_container_width=True
            )

        if search_btn and term.strip():
            term = term.strip()
            st.session_state.term_last = term
            st.session_state.term_explanation = ""
            st.session_state.term_sources = []

            with st.spinner(f"🔍 正在联网搜索「{term}」..."):
                try:
                    search_results = search_term(term)
                    st.session_state.term_sources = search_results
                except Exception as e:
                    st.error(f"搜索失败：{e}")
                    st.stop()

            if not search_results:
                st.warning("未找到相关搜索结果，请尝试其他关键词。")
            else:
                st.success(f"找到 {len(search_results)} 条搜索结果")

                with st.spinner(f"🤖 AI 正在整理「{term}」的解释笔记..."):
                    try:
                        context = _build_search_context(search_results)
                        sp = SYSTEM_PROMPT.replace("{术语名称}", term)
                        user_msg = f"""请为术语「{term}」生成知识笔记。

以下是联网搜索的结果：

{context}"""

                        explanation = chat(
                            [
                                {"role": "system", "content": sp},
                                {"role": "user", "content": user_msg},
                            ]
                        )
                        st.session_state.term_explanation = explanation
                    except Exception as e:
                        st.error(f"AI 生成失败：{e}")
                        st.stop()

        # 展示已生成的结果
        if st.session_state.term_explanation and st.session_state.term_last:
            term = st.session_state.term_last
            sources = st.session_state.term_sources

            st.markdown("---")
            st.markdown(st.session_state.term_explanation)

            with st.expander("📎 搜索来源"):
                for i, r in enumerate(sources, 1):
                    st.write(f"{i}. [{r.title}]({r.url})")

            st.markdown("---")

            already_exists = note_exists(term)
            if already_exists:
                st.info(f"⚠️ 笔记「{term}.md」在 Obsidian 中已存在，保存将覆盖旧版本。")

            col_a, col_b = st.columns([1, 3])
            with col_a:
                if st.button(
                    "💾 保存到 Obsidian", type="secondary", use_container_width=True
                ):
                    try:
                        filepath = save_note(term, st.session_state.term_explanation)
                        source_urls = [r.url for r in sources]
                        insert_term(term, domain="", source_urls=source_urls)
                        st.success(f"✅ 已保存到：{filepath}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"保存失败：{e}")

    # ============================================
    # Tab 2: 浏览术语库
    # ============================================
    with tab2:
        search_query = st.text_input(
            "搜索已有术语",
            placeholder="输入关键词搜索 Obsidian 术语库...",
            key="browse_search",
        )

        if search_query.strip():
            results = search_notes(search_query.strip())
            if not results:
                st.info("未找到匹配的术语笔记。")
            else:
                st.success(f"找到 {len(results)} 条匹配笔记")
                for r in results:
                    with st.expander(f"📄 {r['term']} — {r['modified']}"):
                        if st.button("📖 查看完整笔记", key=f"view_{r['term']}"):
                            content = read_note(r["term"])
                            if content:
                                st.markdown(content)
                            else:
                                st.warning("无法读取笔记内容。")
                        st.caption(f"摘要：{r['preview']}")
        else:
            all_notes = list_notes()
            db_terms = list_terms(limit=100)

            if not all_notes:
                st.info("术语库为空，去「搜索新术语」页面创建第一条笔记吧！")
            else:
                col_note, col_db = st.columns(2)
                with col_note:
                    st.subheader(f"📝 Obsidian 笔记（{len(all_notes)} 条）")
                    for n in all_notes:
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            if st.button(f"📄 {n['term']}", key=f"obs_{n['term']}"):
                                content = read_note(n["term"])
                                if content:
                                    st.markdown(content)
                        with c2:
                            st.caption(n["modified"])

                with col_db:
                    st.subheader(f"🗄️ 索引记录（{len(db_terms)} 条）")
                    for t in db_terms:
                        st.write(f"- {t['term']}")
                        st.caption(f"  {t['updated_at']}")


if __name__ == "__main__":
    show()
