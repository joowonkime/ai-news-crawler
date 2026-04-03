import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_HISTORY_WEBHOOK_URL = os.getenv("DISCORD_HISTORY_WEBHOOK_URL", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "news.db")

VALID_TAGS = ["신기능", "버그픽스", "성능", "브레이킹", "발표", "기타"]
IMPORTANCE_THRESHOLD = int(os.getenv("IMPORTANCE_THRESHOLD", "6"))

SOURCES = {
    "claude-code": {
        "name": "Claude Code",
        "color": 0x5865F2,
        "tier": "rss",
        "url": "https://github.com/anthropics/claude-code/releases.atom",
    },
    "copilot": {
        "name": "Copilot",
        "color": 0x6E7681,
        "tier": "rss",
        "url": "https://github.blog/changelog/label/copilot/feed/",
    },
    "codex": {
        "name": "Codex",
        "color": 0x10A37F,
        "tier": "rss",
        "url": "https://github.com/openai/codex/releases.atom",
    },
    "openai-blog": {
        "name": "OpenAI Blog",
        "color": 0x412991,
        "tier": "rss",
        "url": "https://openai.com/news/rss.xml",
    },
    "kiro": {
        "name": "Kiro",
        "color": 0xF1C40F,
        "tier": "rss",
        "url": "https://kiro.dev/changelog/feed.rss",
    },
    "windsurf-blog": {
        "name": "Windsurf Blog",
        "color": 0x1ABC9C,
        "tier": "rss",
        "url": "https://windsurf.com/feed.xml",
    },
    "aider": {
        "name": "Aider",
        "color": 0x2ECC71,
        "tier": "rss",
        "url": "https://github.com/Aider-AI/aider/releases.atom",
    },
    "anthropic-blog": {
        "name": "Anthropic Blog",
        "color": 0xD4A574,
        "tier": "html",
        "url": "https://www.anthropic.com/news",
    },
    "cursor": {
        "name": "Cursor",
        "color": 0x9B59B6,
        "tier": "html",
        "url": "https://cursor.com/changelog",
    },
    "windsurf-changelog": {
        "name": "Windsurf Changelog",
        "color": 0x1ABC9C,
        "tier": "html",
        "url": "https://windsurf.com/changelog",
    },
    "devin": {
        "name": "Devin",
        "color": 0xE67E22,
        "tier": "html",
        "url": "https://docs.devin.ai/release-notes/overview",
    },
    "threads-choi": {
        "name": "Threads @choi.openai",
        "color": 0x000000,
        "tier": "playwright",
        "url": "https://www.threads.com/@choi.openai",
    },
}
