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

ROLE_COLORS = {
    "researcher": 0x3498DB,   # Blue
    "practitioner": 0x2ECC71, # Green
    "devil": 0xE74C3C,        # Red
    "judge": 0x9B59B6,        # Purple
}

ROLE_EMOJIS = {
    "researcher": "\U0001f52c",
    "practitioner": "\U0001f6e0\ufe0f",
    "devil": "\U0001f608",
    "judge": "\u2696\ufe0f",
}


def build_forum_post_body(article: dict, title_ko: str = "") -> dict:
    title = title_ko if title_ko else article.get("title", "제목 없음")
    if len(title) > 100:
        title = title[:97] + "..."
    url = article.get("url", "")
    points = article.get("points", 0)
    date = article.get("created_at", "")[:10]
    orig_title = article.get("title", "")
    content = f"\U0001f4c5 {date}  |  \U0001f53a {points} points\n\U0001f517 [{orig_title}]({url})"
    return {"thread_name": title, "content": content}


def build_debate_comment(round_num, role: str, content: str) -> str:
    label = ROLE_LABELS.get(role, role)
    if role == "judge":
        header = "**[Judge \uc885\ud569 \ud310\uc815]**"
    else:
        header = f"**[Round {round_num} - {label}]**"
    return f"{header}\n\n{content}"


def build_debate_embed(round_num, role: str, content: str) -> dict:
    label = ROLE_LABELS.get(role, role)
    emoji = ROLE_EMOJIS.get(role, "")
    color = ROLE_COLORS.get(role, 0x95A5A6)

    if role == "judge":
        return _build_judge_embed(content)

    author_name = f"{emoji} Round {round_num} - {label}"

    if len(content) > 4096:
        content = content[:4093] + "..."

    return {
        "color": color,
        "author": {"name": author_name},
        "description": content,
        "footer": {"text": f"Round {round_num}/3"},
    }


def _build_judge_embed(content: str) -> dict:
    sections = {
        "\uce74\ud14c\uace0\ub9ac": "",
        "\uae30\uc220\uc801 \ud601\uc2e0\ub3c4": "",
        "\uc2e4\ubb34 \uc801\uc6a9 \uac00\ub2a5\uc131": "",
        "\uc5c5\uacc4 \uc601\ud5a5\ub825": "",
        "\ucd5c\uc885 \uc694\uc57d": "",
    }
    current_key = None
    leftover = []

    for line in content.split("\n"):
        matched = False
        for key in sections:
            if line.startswith(key + ":"):
                current_key = key
                sections[key] = line.split(":", 1)[1].strip()
                matched = True
                break
        if not matched:
            if current_key and line.strip():
                sections[current_key] += "\n" + line.strip()
            elif line.strip():
                leftover.append(line.strip())

    fields = []
    if sections["\uce74\ud14c\uace0\ub9ac"]:
        fields.append({"name": "\U0001f3f7\ufe0f \uce74\ud14c\uace0\ub9ac", "value": sections["\uce74\ud14c\uace0\ub9ac"], "inline": True})
    if sections["\uae30\uc220\uc801 \ud601\uc2e0\ub3c4"]:
        fields.append({"name": "\u200b", "value": "**\U0001f4a1 \uae30\uc220\uc801 \ud601\uc2e0\ub3c4**\n\n" + sections["\uae30\uc220\uc801 \ud601\uc2e0\ub3c4"], "inline": False})
    if sections["\uc2e4\ubb34 \uc801\uc6a9 \uac00\ub2a5\uc131"]:
        fields.append({"name": "\u200b", "value": "**\U0001f3ed \uc2e4\ubb34 \uc801\uc6a9 \uac00\ub2a5\uc131**\n\n" + sections["\uc2e4\ubb34 \uc801\uc6a9 \uac00\ub2a5\uc131"], "inline": False})
    if sections["\uc5c5\uacc4 \uc601\ud5a5\ub825"]:
        fields.append({"name": "\u200b", "value": "**\U0001f30d \uc5c5\uacc4 \uc601\ud5a5\ub825**\n\n" + sections["\uc5c5\uacc4 \uc601\ud5a5\ub825"], "inline": False})
    if sections["\ucd5c\uc885 \uc694\uc57d"]:
        fields.append({"name": "\u200b", "value": "**\u2728 \ucd5c\uc885 \uc694\uc57d**\n\n" + sections["\ucd5c\uc885 \uc694\uc57d"], "inline": False})

    embed = {
        "color": ROLE_COLORS["judge"],
        "author": {"name": f"{ROLE_EMOJIS['judge']} Judge \uc885\ud569 \ud310\uc815"},
    }
    if fields:
        embed["fields"] = fields
    else:
        if len(content) > 4096:
            content = content[:4093] + "..."
        embed["description"] = content

    if leftover and not fields:
        pass
    elif leftover:
        embed["description"] = "\n".join(leftover)

    return embed


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
    title_ko: str = "",
    webhook_url: str = DISCORD_FORUM_WEBHOOK_URL,
) -> str | None:
    body = build_forum_post_body(article, title_ko=title_ko)
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


def post_embed_to_thread(
    thread_id: str,
    embed: dict,
    webhook_url: str = DISCORD_FORUM_WEBHOOK_URL,
) -> bool:
    for attempt in range(3):
        resp = requests.post(
            f"{webhook_url}?thread_id={thread_id}",
            json={"embeds": [embed]},
            timeout=15,
        )
        if resp.status_code in (200, 204):
            return True
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 2)
            logger.warning("Rate limited, waiting %s seconds", retry_after)
            time.sleep(retry_after)
            continue
        logger.error("Embed failed: %s %s", resp.status_code, resp.text)
        return False
    return False


def post_full_debate(
    article: dict,
    debate: dict,
    tag_name: str,
    title_ko: str = "",
    webhook_url: str = DISCORD_FORUM_WEBHOOK_URL,
    delay: float = 1.0,
) -> str | None:
    thread_id = create_forum_post(article, tag_name, title_ko=title_ko, webhook_url=webhook_url)
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
    prev_round = None
    for round_num, role in rounds_order:
        round_key = str(round_num)
        if round_key not in rounds or role not in rounds[round_key]:
            continue
        if prev_round is not None and str(round_num) != str(prev_round):
            post_comment_to_thread(thread_id, f"{'─' * 30}", webhook_url)
            time.sleep(delay)
        embed = build_debate_embed(round_num, role, rounds[round_key][role])
        success = post_embed_to_thread(thread_id, embed, webhook_url)
        if not success:
            logger.error("Failed to post embed R%s %s for %s", round_num, role, article["title"][:30])
        prev_round = round_num
        time.sleep(delay)

    logger.info("Full debate posted: %s", article["title"][:50])
    return thread_id
