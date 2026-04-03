import json
import os
from unittest.mock import patch
from debate_engine import (
    load_progress,
    save_progress,
    init_progress,
    save_debate_round,
    load_debate,
    get_pending_articles,
    update_article_status,
    FORUM_TAGS,
)


def test_init_progress(tmp_path):
    articles_path = tmp_path / "articles.json"
    articles_path.write_text(json.dumps({
        "111": {"objectID": "111", "title": "Test 1", "url": "https://a.com", "points": 200, "created_at": "2024-11-07T00:00:00Z"},
        "222": {"objectID": "222", "title": "Test 2", "url": "https://b.com", "points": 150, "created_at": "2024-11-19T00:00:00Z"},
    }), encoding="utf-8")
    progress_path = str(tmp_path / "progress.json")

    progress = init_progress(str(articles_path), progress_path)
    assert progress["total"] == 2
    assert progress["completed"] == 0
    assert "111" in progress["articles"]
    assert progress["articles"]["111"]["status"] == "pending"


def test_load_progress_missing_returns_none(tmp_path):
    result = load_progress(str(tmp_path / "nonexistent.json"))
    assert result is None


def test_save_and_load_progress(tmp_path):
    path = str(tmp_path / "progress.json")
    data = {"total": 2, "completed": 0, "articles": {"111": {"status": "pending"}}}
    save_progress(path, data)
    loaded = load_progress(path)
    assert loaded["total"] == 2
    assert loaded["articles"]["111"]["status"] == "pending"


def test_save_debate_round(tmp_path):
    debates_dir = str(tmp_path / "debates")
    os.makedirs(debates_dir)
    save_debate_round(debates_dir, "111", 1, "researcher", "기술 분석 내용입니다.")
    debate = load_debate(debates_dir, "111")
    assert debate["rounds"]["1"]["researcher"] == "기술 분석 내용입니다."


def test_save_debate_round_accumulates(tmp_path):
    debates_dir = str(tmp_path / "debates")
    os.makedirs(debates_dir)
    save_debate_round(debates_dir, "111", 1, "researcher", "연구자 분석")
    save_debate_round(debates_dir, "111", 1, "practitioner", "실무자 분석")
    save_debate_round(debates_dir, "111", 1, "devil", "반론")
    debate = load_debate(debates_dir, "111")
    assert debate["rounds"]["1"]["researcher"] == "연구자 분석"
    assert debate["rounds"]["1"]["practitioner"] == "실무자 분석"
    assert debate["rounds"]["1"]["devil"] == "반론"


def test_save_judge(tmp_path):
    debates_dir = str(tmp_path / "debates")
    os.makedirs(debates_dir)
    save_debate_round(debates_dir, "111", 1, "researcher", "분석")
    save_debate_round(debates_dir, "111", "judge", "judge", "종합 판정")
    debate = load_debate(debates_dir, "111")
    assert debate["rounds"]["judge"]["judge"] == "종합 판정"


def test_get_pending_articles(tmp_path):
    progress = {
        "total": 3,
        "completed": 1,
        "articles": {
            "111": {"status": "posted"},
            "222": {"status": "pending"},
            "333": {"status": "pending"},
        },
    }
    articles = {
        "111": {"objectID": "111", "title": "Done", "points": 300, "created_at": "2024-11-01T00:00:00Z"},
        "222": {"objectID": "222", "title": "Todo 1", "points": 200, "created_at": "2024-11-05T00:00:00Z"},
        "333": {"objectID": "333", "title": "Todo 2", "points": 100, "created_at": "2024-11-10T00:00:00Z"},
    }
    pending = get_pending_articles(progress, articles, batch_size=2)
    assert len(pending) == 2
    assert pending[0]["objectID"] == "222"


def test_update_article_status():
    progress = {
        "total": 1,
        "completed": 0,
        "posted_to_discord": 0,
        "articles": {"111": {"status": "pending", "rounds_done": 0, "judge_done": False, "posted": False, "thread_id": None}},
    }
    update_article_status(progress, "111", status="debating", rounds_done=1)
    assert progress["articles"]["111"]["status"] == "debating"
    assert progress["articles"]["111"]["rounds_done"] == 1


def test_forum_tags_has_14_entries():
    assert len(FORUM_TAGS) == 14
    assert "Dev - MCP" in FORUM_TAGS
    assert "Model - 모델 출시" in FORUM_TAGS
