import logging
import feedparser
import requests

logger = logging.getLogger(__name__)


def parse_feed(xml_text: str, source_key: str, max_items: int = 20) -> list[dict]:
    if not xml_text.strip():
        return []
    feed = feedparser.parse(xml_text)
    if feed.bozo and not feed.entries:
        logger.warning("Malformed feed for %s: %s", source_key, feed.bozo_exception)
        return []

    articles = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            continue

        content = ""
        if entry.get("content"):
            content = entry.content[0].get("value", "")
        elif entry.get("summary"):
            content = entry.summary

        published = entry.get("published", entry.get("updated", ""))

        articles.append({
            "source": source_key,
            "title": title,
            "url": link,
            "content": content,
            "published_at": published,
        })

    return articles[:max_items]


def fetch_rss(url: str, source_key: str, max_items: int = 20) -> list[dict]:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return parse_feed(resp.text, source_key, max_items=max_items)
    except Exception as e:
        logger.error("Failed to fetch RSS %s: %s", url, e)
        return []
