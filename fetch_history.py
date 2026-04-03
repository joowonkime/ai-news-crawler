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


HN_COLOR = 0xFF6600


def build_history_embed(story: dict) -> dict:
    created = story.get("created_at", "")[:10]
    points = story.get("points", 0)
    reason = story.get("reason", "")
    summary = story.get("summary", "")
    tags_raw = story.get("tags", "기타")

    tag_str = " ".join(f"`{t.strip()}`" for t in tags_raw.split(",") if t.strip())

    description_parts = [f"\U0001f4c5 {created}  |  \U0001f53a {points} points"]
    if reason:
        description_parts.append(f"\n\U0001f4a1 {reason}")
    if summary:
        description_parts.append(f"\n{summary}")
    if tag_str:
        description_parts.append(f"\n{tag_str}")

    description = "\n".join(description_parts)
    if len(description) > 2048:
        description = description[:2045] + "..."

    return {
        "author": {"name": "Hacker News"},
        "title": story.get("title", ""),
        "url": story.get("url", ""),
        "description": description,
        "color": HN_COLOR,
        "footer": {"text": created},
    }


def post_history_to_discord(
    summarized: dict,
    webhook_url: str = DISCORD_HISTORY_WEBHOOK_URL,
    delay: float = 1.0,
):
    sorted_stories = sorted(summarized.values(), key=lambda s: s.get("created_at", ""))
    total = len(sorted_stories)
    posted = 0

    for i, story in enumerate(sorted_stories, 1):
        embed = build_history_embed(story)
        payload = {"embeds": [embed]}

        for attempt in range(3):
            resp = requests.post(webhook_url, json=payload, timeout=15)
            if resp.status_code in (200, 204):
                posted += 1
                logger.info("[%d/%d] Posted: \"%s\"", i, total, story["title"])
                break
            if resp.status_code == 429:
                retry_after = resp.json().get("retry_after", 2)
                logger.warning("Rate limited, waiting %s seconds", retry_after)
                time.sleep(retry_after)
                continue
            logger.error("Discord error %s: %s", resp.status_code, resp.text)
            break

        time.sleep(delay)

    logger.info("Discord posting complete. %d/%d posted.", posted, total)


def main():
    logger.info("=== HN History Fetch 시작 ===")

    logger.info("Step 1: HN Algolia API에서 수집...")
    stories = collect_all_hn_stories()
    logger.info("수집 완료: %d개 고유 기사", len(stories))

    if not stories:
        logger.info("수집된 기사가 없습니다.")
        return

    logger.info("Step 2: 체크포인트 로드 및 Gemini 요약...")
    checkpoint = load_checkpoint()
    summarized = summarize_stories(stories, checkpoint)

    logger.info("Step 3: Discord history 채널에 전송...")
    post_history_to_discord(summarized)

    logger.info("=== 완료 ===")


if __name__ == "__main__":
    main()
