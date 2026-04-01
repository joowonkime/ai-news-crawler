import argparse
import json
import logging
import sys

from config import SOURCES, GEMINI_API_KEY, DISCORD_WEBHOOK_URL, DB_PATH, IMPORTANCE_THRESHOLD
from db import init_db, insert_article, get_unposted, update_summary, mark_posted
from crawlers.rss_crawler import fetch_rss
from crawlers.html_crawler import (
    fetch_html,
    parse_anthropic,
    parse_cursor,
    parse_windsurf,
    parse_devin,
)
from crawlers.threads_crawler import fetch_threads
from summarizer import summarize
from discord_poster import send_to_discord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

HTML_PARSERS = {
    "anthropic-blog": parse_anthropic,
    "cursor": parse_cursor,
    "windsurf-changelog": parse_windsurf,
    "devin": parse_devin,
}


def crawl_source(source_key: str, source_cfg: dict) -> list[dict]:
    tier = source_cfg["tier"]
    url = source_cfg["url"]

    if tier == "rss":
        return fetch_rss(url, source_key)
    elif tier == "html":
        html = fetch_html(url, source_key)
        if not html:
            return []
        parser = HTML_PARSERS.get(source_key)
        if parser:
            return parser(html)
        return []
    elif tier == "playwright":
        return fetch_threads(url)
    return []


def run_pipeline(
    db_path: str = DB_PATH,
    sources: list[str] | None = None,
    webhook_url: str = DISCORD_WEBHOOK_URL,
    api_key: str = GEMINI_API_KEY,
    init_mode: bool = False,
):
    init_db(db_path)

    source_list = sources or list(SOURCES.keys())
    new_count = 0

    for source_key in source_list:
        if source_key not in SOURCES:
            logger.warning("Unknown source: %s", source_key)
            continue

        source_cfg = SOURCES[source_key]
        logger.info("Crawling %s...", source_cfg["name"])
        articles = crawl_source(source_key, source_cfg)
        logger.info("  Found %d articles from %s", len(articles), source_key)

        for article in articles:
            if insert_article(db_path, article):
                new_count += 1

    logger.info("Total new articles: %d", new_count)

    if init_mode:
        logger.info("Init mode: marking all existing articles as posted")
        unposted = get_unposted(db_path)
        for article in unposted:
            mark_posted(db_path, article["id"])
        logger.info("Marked %d articles as posted", len(unposted))
        return

    unposted = get_unposted(db_path)
    logger.info("Unposted articles: %d", len(unposted))

    for article in unposted:
        if api_key:
            result = summarize(article["title"], article.get("content", ""), api_key)
            if not result:
                logger.warning("Skipping post (no summary): %s", article["title"])
                continue

            importance = result.get("importance", 0)
            if importance < IMPORTANCE_THRESHOLD:
                logger.info(
                    "Skipped (importance %d/%d): %s",
                    importance, IMPORTANCE_THRESHOLD, article["title"],
                )
                mark_posted(db_path, article["id"])
                continue

            summary_with_reason = result["summary"]
            if result.get("reason"):
                summary_with_reason = f"💡 {result['reason']}\n\n{result['summary']}"

            update_summary(db_path, article["id"], summary_with_reason, result["tags"], importance)
            article["summary"] = summary_with_reason
            article["tags"] = result["tags"]

        if send_to_discord(webhook_url, article):
            mark_posted(db_path, article["id"])
            logger.info("Posted (importance %s): %s", result.get("importance", "?"), article["title"])
        else:
            logger.error("Failed to post: %s", article["title"])


def main():
    parser = argparse.ArgumentParser(description="AI News Crawler")
    parser.add_argument("--source", type=str, help="Crawl single source only")
    parser.add_argument(
        "--test-webhook", action="store_true", help="Send test message to Discord"
    )
    parser.add_argument(
        "--init", action="store_true",
        help="First run: crawl all sources and mark as posted (no Discord)",
    )
    args = parser.parse_args()

    if args.test_webhook:
        test_article = {
            "source": "claude-code",
            "title": "Test Message",
            "url": "https://example.com/test",
            "summary": "이것은 테스트 메시지입니다.",
            "tags": json.dumps(["기타"]),
            "published_at": "2026-04-01",
        }
        if send_to_discord(DISCORD_WEBHOOK_URL, test_article):
            print("Test message sent!")
        else:
            print("Failed to send test message.")
        return

    sources = [args.source] if args.source else None
    run_pipeline(sources=sources, init_mode=args.init)


if __name__ == "__main__":
    main()
