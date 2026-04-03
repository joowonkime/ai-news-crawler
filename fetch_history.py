# fetch_history.py
import json
import logging
import time
import requests

from config import GEMINI_API_KEY, DISCORD_HISTORY_WEBHOOK_URL
from summarizer import summarize
from discord_poster import send_to_discord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
MCP_RELEASE_TIMESTAMP = 1730419200  # 2024-11-01 UTC
MIN_POINTS = 100
MAX_PAGES = 4
CHECKPOINT_FILE = "history_checkpoint.json"

KEYWORDS = [
    "AI harness",
    "AI agent framework",
    "LLM framework",
    "LLM benchmark",
    "model evaluation",
    "AI benchmark",
    "AI coding",
    "code generation LLM",
    "vibe coding",
    "Claude AI",
    "GPT-5",
    "Gemini Pro",
    "Llama 3",
    "OpenAI o1",
    "OpenAI o3",
    "MCP protocol",
    "tool use AI",
    "function calling LLM",
]


def search_hn(query: str, min_points: int = MIN_POINTS, max_pages: int = MAX_PAGES) -> list[dict]:
    all_hits = []
    for page in range(max_pages):
        params = {
            "query": query,
            "tags": "story",
            "numericFilters": f"points>{min_points},created_at_i>{MCP_RELEASE_TIMESTAMP}",
            "hitsPerPage": 50,
            "page": page,
        }
        resp = requests.get(HN_SEARCH_URL, params=params, timeout=15)
        if resp.status_code != 200:
            logger.warning("HN API error for '%s' page %d: %s", query, page, resp.status_code)
            break
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            break
        all_hits.extend(hits)
        if page + 1 >= data.get("nbPages", 0):
            break
        time.sleep(0.5)
    return all_hits


def collect_all_hn_stories(keywords: list[str] = KEYWORDS) -> list[dict]:
    seen_ids = set()
    all_stories = []
    for kw in keywords:
        logger.info("Searching HN: '%s'", kw)
        hits = search_hn(kw)
        for hit in hits:
            oid = hit["objectID"]
            if oid not in seen_ids:
                seen_ids.add(oid)
                all_stories.append(hit)
        logger.info("  Found %d hits, total unique: %d", len(hits), len(all_stories))
    all_stories.sort(key=lambda h: h.get("created_at_i", 0))
    return all_stories


def load_checkpoint(path: str = CHECKPOINT_FILE) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_checkpoint(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def summarize_stories(
    stories: list[dict],
    checkpoint: dict,
    api_key: str = GEMINI_API_KEY,
    checkpoint_path: str | None = CHECKPOINT_FILE,
    delay: float = 2.0,
) -> dict:
    results = dict(checkpoint)
    total = len(stories)
    skipped = 0

    for i, story in enumerate(stories, 1):
        oid = story["objectID"]
        if oid in results:
            skipped += 1
            continue

        title = story.get("title", "")
        url = story.get("url", "")
        points = story.get("points", 0)
        created_at = story.get("created_at", "")

        logger.info("[%d/%d] Summarizing: \"%s\" (%d points)", i, total, title, points)

        result = summarize(title, f"URL: {url}\nHacker News points: {points}", api_key)
        if result:
            results[oid] = {
                "title": title,
                "url": url,
                "points": points,
                "created_at": created_at,
                "summary": result["summary"],
                "tags": result["tags"],
                "importance": result["importance"],
                "reason": result.get("reason", ""),
            }
        else:
            results[oid] = {
                "title": title,
                "url": url,
                "points": points,
                "created_at": created_at,
                "summary": title,
                "tags": "기타",
                "importance": 0,
                "reason": "",
            }

        if checkpoint_path:
            save_checkpoint(checkpoint_path, results)

        time.sleep(delay)

    logger.info("Summarization complete. %d new, %d skipped (checkpointed)", total - skipped, skipped)
    return results
