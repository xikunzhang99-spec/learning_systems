# 学习系统

AI 驱动的英语学习 + 代码学习一体化平台，基于 Streamlit 构建。

## 功能概览

### 英语场景学习
输入主题名称，AI 自动生成包含 5 个场景的交互式 HTML 学习页面。

- 支持中英文主题输入
- 5 种画面风格可选：现代扁平插画、美漫风格、像素风格、手绘素描、电影概念设计
- 生成的页面包含场景导航、词汇卡片（单词 + 翻译 + 例句）、测验模式
- 历史记录持久化保存

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
- Node.js（用于英语场景学习页面的 CSS 框架生成）

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
├── app.py                  # Streamlit 主入口 / 主页
├── pages/
│   ├── 1_📖_英语场景学习.py  # 英语场景生成页面
│   ├── 2_💻_代码解释.py      # 代码解释页面
│   └── 3_📝_学习记录.py      # 学习记录浏览页面
├── services/               # 业务逻辑层
├── database/               # 数据库初始化与连接
├── config/                 # 配置读取
├── prompts/                # AI Prompt 模板
├── utils/                  # 工具函数
├── src/                    # Node.js 前端生成脚本
├── output/                 # 生成的 HTML 文件
└── data/                   # SQLite 数据库文件
```

## 使用说明

### 英语场景学习
1. 在左侧边栏点击「英语场景学习」
2. 输入主题名称（中英文均可），例如 "A Day at the Beach"
3. 选择画面风格，点击「开始生成」（约需 1-7 分钟）
4. 生成完成后点击「打开」在浏览器中查看交互式页面
5. 在生成的页面上点击场景元素查看词汇卡片，使用方向键切换场景，开启测验模式测试记忆

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
