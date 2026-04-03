"""
멀티에이전트 토론 배치 오케스트레이션.

사용법:
  python run_debate.py --init          # progress 초기화
  python run_debate.py --post          # 완료된 토론을 Discord에 전송
  python run_debate.py --status        # 현재 진행 상태 확인
  python run_debate.py --post-one OID  # 특정 기사 1개 전송

토론 자체는 Claude Code 세션에서 서브에이전트로 수행합니다.
이 스크립트는 진행 관리와 Discord 전송을 담당합니다.
"""
import argparse
import json
import logging
import sys

from debate_engine import (
    load_progress,
    save_progress,
    init_progress,
    load_debate,
    update_article_status,
    PROGRESS_FILE,
    COLLECTED_FILE,
    DEBATES_DIR,
    FORUM_TAGS,
)
from forum_poster import post_full_debate, parse_judge_tag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_init():
    progress = init_progress()
    logger.info("Progress initialized: %d articles", progress["total"])


def cmd_status():
    progress = load_progress()
    if not progress:
        print("No progress file. Run --init first.")
        return
    total = progress["total"]
    completed = progress.get("completed", 0)
    posted = progress.get("posted_to_discord", 0)
    pending = sum(1 for a in progress["articles"].values() if a["status"] == "pending")
    debating = sum(1 for a in progress["articles"].values() if a["status"] == "debating")
    print(f"Total: {total}")
    print(f"Pending: {pending}")
    print(f"Debating: {debating}")
    print(f"Completed (not posted): {completed - posted}")
    print(f"Posted: {posted}")


def cmd_post():
    progress = load_progress()
    if not progress:
        logger.error("No progress file. Run --init first.")
        return

    with open(COLLECTED_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    posted_count = 0
    for oid, state in progress["articles"].items():
        if state["status"] != "completed":
            continue

        debate = load_debate(DEBATES_DIR, oid)
        if not debate:
            logger.warning("No debate file for %s, skipping", oid)
            continue

        article = articles.get(oid, {})
        if not article:
            continue

        judge_text = debate.get("rounds", {}).get("judge", {}).get("judge", "")
        tag_name = parse_judge_tag(judge_text)

        thread_id = post_full_debate(article, debate, tag_name)
        if thread_id:
            update_article_status(progress, oid, status="posted", posted=True, thread_id=thread_id)
            save_progress(PROGRESS_FILE, progress)
            posted_count += 1
            logger.info("[%d] Posted: %s", posted_count, article.get("title", "")[:50])
        else:
            logger.error("Failed to post: %s", article.get("title", "")[:50])

    logger.info("Posting complete. %d articles posted.", posted_count)


def cmd_post_one(object_id: str):
    progress = load_progress()
    if not progress:
        logger.error("No progress file. Run --init first.")
        return

    with open(COLLECTED_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    debate = load_debate(DEBATES_DIR, object_id)
    if not debate:
        logger.error("No debate file for %s", object_id)
        return

    article = articles.get(object_id, {})
    if not article:
        logger.error("Article %s not found", object_id)
        return

    judge_text = debate.get("rounds", {}).get("judge", {}).get("judge", "")
    tag_name = parse_judge_tag(judge_text)

    thread_id = post_full_debate(article, debate, tag_name)
    if thread_id:
        update_article_status(progress, object_id, status="posted", posted=True, thread_id=thread_id)
        save_progress(PROGRESS_FILE, progress)
        logger.info("Posted: %s (thread: %s)", article.get("title", "")[:50], thread_id)
    else:
        logger.error("Failed to post: %s", article.get("title", "")[:50])


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Debate Orchestration")
    parser.add_argument("--init", action="store_true", help="Initialize progress from collected articles")
    parser.add_argument("--status", action="store_true", help="Show current progress")
    parser.add_argument("--post", action="store_true", help="Post completed debates to Discord")
    parser.add_argument("--post-one", type=str, help="Post a single article by objectID")
    args = parser.parse_args()

    if args.init:
        cmd_init()
    elif args.status:
        cmd_status()
    elif args.post:
        cmd_post()
    elif args.post_one:
        cmd_post_one(args.post_one)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
