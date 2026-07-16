import streamlit as st
import sys
import os

from services.theme_service import generate_theme_stream, list_generations, delete_generation

# Style mapping
STYLE_OPTIONS = {
    "现代扁平插画 (Flat Design)": "flat design",
    "美漫风格 (American Comic)": "american comic",
    "像素风格 (Pixel Art)": "pixel art",
    "手绘素描 (Hand-drawn Sketch)": "hand-drawn sketch",
    "电影概念设计 (Cinematic Concept Art)": "cinematic concept art",
}


def show():
    st.title("📖 英语场景学习")
    st.caption("通过 AI 生成交互式英语学习场景页面")

    # --- 生成新主题 ---
    st.header("生成新主题", divider="blue")

    col1, col2 = st.columns([3, 2])
    with col1:
        theme_name = st.text_input(
            "主题名称",
            placeholder="例如：A Day at the Beach、海滩的一天、Space Adventure",
            key="theme_input",
        )
    with col2:
        style_label = st.selectbox("画面风格", list(STYLE_OPTIONS.keys()), key="style_select")
        style_value = STYLE_OPTIONS[style_label]

    gen_clicked = st.button("🚀 开始生成", type="primary")

    if gen_clicked:
        if not theme_name.strip():
            st.error("请输入主题名称。")
        else:
            log_expander = st.expander("生成日志", expanded=True)
            log_placeholder = log_expander.empty()
            status = st.status("正在生成...", expanded=True)

            logs = []

            for line in generate_theme_stream(theme_name.strip(), style_value):
                logs.append(line)
                log_placeholder.code("\n".join(logs[-40:]))
                if any(kw in line for kw in ["Scene", "Phase", "Done", "Output", "Error"]):
                    status.update(label=line[:120])

            # 解析输出路径
            result_path = None
            for line in logs:
                if "Output:" in line:
                    result_path = line.split("Output:", 1)[-1].strip()
                    break

            if result_path and os.path.isfile(result_path):
                status.update(label="✅ 生成完成！", state="complete")
                st.success(f"文件已保存：`{result_path}`")
                if st.button("📂 打开生成的页面", key="open_generated"):
                    _open_file(result_path)
            else:
                status.update(label="❌ 生成失败 — 请查看日志", state="error")
                st.error("未找到输出文件，请查看日志排查问题。")

    # --- 历史记录 ---
    st.header("历史记录", divider="green")

    generations = list_generations()

    if not generations:
        st.info("暂无历史记录，在上面生成第一个主题吧！")
    else:
        for gen in generations:
            fpath = gen["output_path"]
            fname = os.path.basename(fpath)
            exists = os.path.isfile(fpath)

            cols = st.columns([3, 2, 2, 1, 0.8])
            with cols[0]:
                st.markdown(f"**{gen['theme_name']}**")
                st.caption(fname)
            with cols[1]:
                st.caption(gen["style"])
            with cols[2]:
                ts = gen.get("created_at", "")[:16].replace("T", " ")
                st.caption(ts)
            with cols[3]:
                if exists:
                    if st.button("📂 打开", key=f"open_{gen['id']}", use_container_width=True):
                        _open_file(fpath)
                else:
                    st.caption("文件缺失")
            with cols[4]:
                if st.button("✕", key=f"del_gen_{gen['id']}", help="从历史中移除"):
                    delete_generation(gen["id"])
                    st.rerun()

    # --- 使用说明 ---
    with st.expander("ℹ️ 使用说明"):
        st.markdown("""
        1. 输入一个**主题名称**（支持中英文）— 例如 "A Day at the Beach" 或 "海滩的一天"
        2. 从下拉菜单中选择**画面风格**
        3. 点击**开始生成** — AI 将创建包含 5 个场景的交互式学习页面（约需 1-7 分钟）
        4. 点击**打开**在浏览器中查看生成的页面
        5. 在生成的页面上：
           - 点击场景元素查看词汇卡片（单词 + 翻译 + 例句）
           - 使用方向键 / Ctrl+方向键切换场景
           - 开启**测验模式**隐藏中文翻译，测试记忆

        历史记录会持久化保存，重启应用不会丢失。文件保存在 `output/` 文件夹中。
        """)


def _open_file(filepath):
    """跨平台打开文件。"""
    if sys.platform == "darwin":
        import subprocess
        subprocess.run(["open", filepath])
    elif sys.platform == "win32":
        os.startfile(filepath)
    else:
        import subprocess
        subprocess.run(["xdg-open", filepath])


if __name__ == "__main__":
    show()
