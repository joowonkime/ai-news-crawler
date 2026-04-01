import json
import time
import logging
import requests
from config import SOURCES

logger = logging.getLogger(__name__)


def build_embed(article: dict) -> dict:
    source_key = article["source"]
    source_cfg = SOURCES.get(source_key, {"name": source_key, "color": 0x95A5A6})

    summary = article.get("summary") or article.get("content") or ""
    tags_raw = article.get("tags")
    if tags_raw:
        try:
            tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
            tag_str = " ".join(f"`{t}`" for t in tags)
            description = f"{summary}\n\n{tag_str}"
        except (json.JSONDecodeError, TypeError):
            description = summary
    else:
        description = summary

    if len(description) > 2048:
        description = description[:2045] + "..."

    return {
        "author": {"name": source_cfg["name"]},
        "title": article["title"],
        "url": article["url"],
        "description": description,
        "color": source_cfg["color"],
        "footer": {"text": article.get("published_at", "")},
    }


def send_to_discord(webhook_url: str, article: dict, max_retries: int = 3) -> bool:
    embed = build_embed(article)
    payload = {"embeds": [embed]}

    for attempt in range(max_retries):
        resp = requests.post(webhook_url, json=payload)
        if resp.status_code in (200, 204):
            return True
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 1)
            logger.warning("Rate limited, retrying after %s seconds", retry_after)
            time.sleep(retry_after)
            continue
        logger.error("Discord webhook failed: %s %s", resp.status_code, resp.text)
        return False

    return False
