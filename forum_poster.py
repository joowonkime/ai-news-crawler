import json
import logging
import time
import requests

from config import DISCORD_FORUM_WEBHOOK_URL
from debate_engine import FORUM_TAGS

logger = logging.getLogger(__name__)

ROLE_LABELS = {
    "researcher": "Researcher",
    "practitioner": "Practitioner",
    "devil": "Devil's Advocate",
    "judge": "Judge",
}


def build_forum_post_body(article: dict) -> dict:
    title = article.get("title", "제목 없음")
    if len(title) > 100:
        title = title[:97] + "..."
    url = article.get("url", "")
    points = article.get("points", 0)
    date = article.get("created_at", "")[:10]
    content = f"\U0001f4c5 {date}  |  \U0001f53a {points} points\n{url}"
    return {"thread_name": title, "content": content}


def build_debate_comment(round_num, role: str, content: str) -> str:
    label = ROLE_LABELS.get(role, role)
    if role == "judge":
        header = "**[Judge \uc885\ud569 \ud310\uc815]**"
    else:
        header = f"**[Round {round_num} - {label}]**"
    return f"{header}\n\n{content}"


def parse_judge_tag(judge_text: str) -> str:
    for line in judge_text.split("\n"):
        if line.startswith("\uce74\ud14c\uace0\ub9ac:"):
            tag_name = line.replace("\uce74\ud14c\uace0\ub9ac:", "").strip()
            if tag_name in FORUM_TAGS:
                return tag_name
    return "Community - \uc758\uacac/\ud1a0\ub860"


def create_forum_post(
    article: dict,
    tag_name: str,
    webhook_url: str = DISCORD_FORUM_WEBHOOK_URL,
) -> str | None:
    body = build_forum_post_body(article)
    tag_id = FORUM_TAGS.get(tag_name)
    if tag_id:
        body["applied_tags"] = [tag_id]

    for attempt in range(3):
        resp = requests.post(f"{webhook_url}?wait=true", json=body, timeout=15)
        if resp.status_code in (200, 204):
            data = resp.json()
            thread_id = data.get("channel_id", "")
            logger.info("Forum post created: %s (thread: %s)", article["title"][:50], thread_id)
            return thread_id
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 2)
            logger.warning("Rate limited, waiting %s seconds", retry_after)
            time.sleep(retry_after)
            continue
        logger.error("Forum post failed: %s %s", resp.status_code, resp.text)
        return None
    return None


def post_comment_to_thread(
    thread_id: str,
    content: str,
    webhook_url: str = DISCORD_FORUM_WEBHOOK_URL,
) -> bool:
    if len(content) > 2000:
        content = content[:1997] + "..."

    for attempt in range(3):
        resp = requests.post(
            f"{webhook_url}?thread_id={thread_id}",
            json={"content": content},
            timeout=15,
        )
        if resp.status_code in (200, 204):
            return True
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 2)
            logger.warning("Rate limited, waiting %s seconds", retry_after)
            time.sleep(retry_after)
            continue
        logger.error("Comment failed: %s %s", resp.status_code, resp.text)
        return False
    return False


def post_full_debate(
    article: dict,
    debate: dict,
    tag_name: str,
    webhook_url: str = DISCORD_FORUM_WEBHOOK_URL,
    delay: float = 1.0,
) -> str | None:
    thread_id = create_forum_post(article, tag_name, webhook_url)
    if not thread_id:
        return None

    time.sleep(delay)

    rounds_order = [
        (1, "researcher"), (1, "practitioner"), (1, "devil"),
        (2, "researcher"), (2, "practitioner"), (2, "devil"),
        (3, "researcher"), (3, "practitioner"), (3, "devil"),
        ("judge", "judge"),
    ]

    rounds = debate.get("rounds", {})
    for round_num, role in rounds_order:
        round_key = str(round_num)
        if round_key in rounds and role in rounds[round_key]:
            comment = build_debate_comment(round_num, role, rounds[round_key][role])
            success = post_comment_to_thread(thread_id, comment, webhook_url)
            if not success:
                logger.error("Failed to post comment R%s %s for %s", round_num, role, article["title"][:30])
            time.sleep(delay)

    logger.info("Full debate posted: %s", article["title"][:50])
    return thread_id
