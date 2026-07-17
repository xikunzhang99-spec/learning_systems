# 学习系统

AI 驱动的英语学习 + 代码学习 + 术语解释一体化平台，基于 Streamlit 构建。

## 功能概览

### 英语学习
基于个人表达库的结构化场景学习系统。新工作流：创建主题 → 录入学习素材 → AI 生成场景剧本 → 编辑分镜 → 可视化学习与复习。

- 按日期和主题管理学习素材（单词、短语、表达、句子）
- AI 生成 4-6 格结构化场景剧本和分镜
- 多镜头故事板：4 种布局模板，分镜编辑与重生成
- 三种复习模式：隐藏中文、隐藏英文、看图回忆
- 掌握程度跟踪（0-3 星）

### 代码解释
输入代码片段，AI 流式输出逐行解释。

- 自动识别代码语言（Python / JavaScript / Shell / SQL / HTML / CSS 等）
- 三种解释深度：简单解释、详细解释、教学式解释
- 流式实时输出，无需等待完整响应
- 解释完成后自动保存到学习记录

### 学习记录
查看和管理历史代码解释记录。

- 关键词搜索（代码内容 / 摘要 / AI 解释）
- 按编程语言筛选
- 展开查看完整原始代码和 AI 解释
- 支持删除记录

## 环境要求

- Python 3.10+

## 安装与运行

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
# 复制 .env.example 为 .env，填入对应 API Key

# 4. 启动应用
streamlit run app.py
```

启动后浏览器访问 `http://localhost:8501`。

## 环境变量

在项目根目录创建 `.env` 文件：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_PROVIDER` | AI 服务商：`openai` / `deepseek` / `claude` | `openai` |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OPENAI_MODEL` | OpenAI 模型 | `gpt-4o-mini` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | `deepseek-chat` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `CLAUDE_API_KEY` | Claude API Key | - |
| `CLAUDE_MODEL` | Claude 模型 | `claude-sonnet-4-6` |
| `DATABASE_PATH` | SQLite 数据库路径 | `data/learning.db` |

## 项目结构

```
学习系统/
├── app.py                      # Streamlit 主入口 / 主页
├── pages/
│   ├── 1_📖_英语学习.py          # 英语学习：话题→素材→场景→复习
│   ├── 2_💻_代码解释.py          # 代码解释页面
│   └── 3_📡_专业术语解释.py      # 术语解释页面
├── services/                   # 业务逻辑层
│   ├── topic_service.py        # 学习话题 CRUD
│   ├── item_service.py         # 学习素材 CRUD
│   ├── scene_service.py        # 场景脚本生成与编辑
│   ├── storyboard_renderer.py  # 故事板渲染（4 种模板）
│   ├── ai_service.py           # AI Provider 统一接口
│   ├── theme_service.py        # [已弃用] 旧版场景生成
│   └── ...
├── database/                   # 数据库初始化与连接
├── config/                     # 配置读取
├── prompts/                    # AI Prompt 模板
│   ├── scene_script_prompt.py  # 场景脚本 Prompt 与 Schema
│   └── code_tutor_prompt.py    # 代码解释 Prompt
├── utils/                      # 工具函数
├── _legacy/                    # 旧版 Node.js 代码（已归档）
├── output/                     # 旧版生成的 HTML 文件
└── data/                       # SQLite 数据库文件
```

## 使用说明

### 英语学习
1. 在左侧边栏点击「英语学习」
2. 创建学习话题（如 "Daily Office English"），设置日期、标签
3. 在话题中添加学习素材（单词、短语、表达、句子）— 支持批量导入
4. 选择本次要学习的素材，点击「生成场景」
5. AI 生成 4-5 格结构化场景剧本，预览和编辑每个分镜
6. 确认后进入学习页面，切换三种复习模式巩固记忆

### 代码解释
1. 在左侧边栏点击「代码解释」
2. 粘贴代码到输入框
3. 选择代码语言（或使用自动识别）和解释深度
4. 点击「开始解释代码」，AI 将流式输出分析结果
5. 解释内容自动保存，可在「学习记录」页面查看

### 学习记录
1. 在左侧边栏点击「学习记录」
2. 通过关键词搜索或按语言筛选历史记录
3. 点击记录展开查看完整代码和 AI 解释
4. 可删除不需要的记录
