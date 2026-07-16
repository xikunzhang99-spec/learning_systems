import streamlit as st
from database.db import init_db

st.set_page_config(
    page_title="学习系统",
    page_icon="📚",
    layout="wide",
)

# 初始化数据库（缓存，仅执行一次）
@st.cache_resource
def _init_database():
    init_db()
    return True

_init_database()

# ---- 主页 ----
st.title("📚 学习系统")
st.caption("AI 驱动的英语学习 + 代码学习 + 术语解释一体化平台")

st.markdown("---")

# 快速入口
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📖 英语场景学习
    通过 AI 生成交互式英语学习场景页面。
    - 输入主题，自动生成 5 个故事场景
    - 点击场景元素查看词汇卡片
    - 支持 5 种画面风格
    - 测验模式测试记忆
    """)

with col2:
    st.markdown("""
    ### 💻 代码解释
    AI 逐行解释代码逻辑和知识点。
    - 自动识别代码语言
    - 三种解释深度可选
    - 流式实时输出
    - 自动保存学习记录
    """)

with col3:
    st.markdown("""
    ### 📡 专业术语解释
    联网搜索并自动生成术语知识笔记。
    - 输入术语/缩写，自动联网搜索
    - AI 生成结构化通俗解释
    - 一键保存到 Obsidian
    - 浏览和搜索术语库
    """)

st.markdown("---")
st.caption("👈 从左侧边栏选择功能页面开始使用")
