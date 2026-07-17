import os
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Claude
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Database
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "data", "learning.db")
)

# Term Radar - Tavily Search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Term Radar - Obsidian
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "")
OBSIDIAN_NOTE_FOLDER = os.getenv("OBSIDIAN_NOTE_FOLDER", "术语库")

# Output (legacy, kept for existing saved files)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Image Generation
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "").lower()
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "")
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1024")
