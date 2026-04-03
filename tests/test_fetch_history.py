import json
from unittest.mock import patch, MagicMock
from fetch_history import search_hn, collect_all_hn_stories, KEYWORDS
from fetch_history import load_checkpoint, save_checkpoint, summarize_stories
from fetch_history import build_history_embed

# HN Algolia API 응답 fixture
FAKE_HN_RESPONSE = {
    "hits": [
        {
            "objectID": "111",
            "title": "Claude AI releases MCP",
            "url": "https://example.com/mcp",
            "points": 250,
            "created_at_i": 1731000000,
            "created_at": "2024-11-07T00:00:00Z",
        },
        {
            "objectID": "222",
            "title": "GPT-5 benchmark results",
            "url": "https://example.com/gpt5",
            "points": 180,
            "created_at_i": 1732000000,
            "created_at": "2024-11-19T00:00:00Z",
        },
    ],
    "nbPages": 1,
}

FAKE_HN_EMPTY = {"hits": [], "nbPages": 0}


@patch("fetch_history.requests.get")
def test_search_hn_returns_hits(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = FAKE_HN_RESPONSE
    mock_get.return_value = mock_resp

    results = search_hn("Claude AI", min_points=100)
    assert len(results) == 2
    assert results[0]["objectID"] == "111"
    assert results[0]["points"] == 250


@patch("fetch_history.requests.get")
def test_search_hn_paginates(mock_get):
    page0 = {
        "hits": [{"objectID": "111", "title": "A", "url": "https://a.com", "points": 200, "created_at_i": 1731000000, "created_at": "2024-11-07T00:00:00Z"}],
        "nbPages": 2,
    }
    page1 = {
        "hits": [{"objectID": "222", "title": "B", "url": "https://b.com", "points": 150, "created_at_i": 1732000000, "created_at": "2024-11-19T00:00:00Z"}],
        "nbPages": 2,
    }
    mock_resp0 = MagicMock()
    mock_resp0.status_code = 200
    mock_resp0.json.return_value = page0
    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = page1
    mock_get.side_effect = [mock_resp0, mock_resp1]

    results = search_hn("AI", min_points=100, max_pages=2)
    assert len(results) == 2


@patch("fetch_history.search_hn")
def test_collect_all_deduplicates(mock_search):
    shared_hit = {"objectID": "111", "title": "Shared", "url": "https://shared.com", "points": 300, "created_at_i": 1731000000, "created_at": "2024-11-07T00:00:00Z"}
    unique_hit = {"objectID": "222", "title": "Unique", "url": "https://unique.com", "points": 150, "created_at_i": 1732000000, "created_at": "2024-11-19T00:00:00Z"}
    mock_search.side_effect = [[shared_hit], [shared_hit, unique_hit]]

    results = collect_all_hn_stories(keywords=["kw1", "kw2"])
    assert len(results) == 2
    ids = {r["objectID"] for r in results}
    assert ids == {"111", "222"}


def test_checkpoint_roundtrip(tmp_path):
    path = str(tmp_path / "cp.json")
    save_checkpoint(path, {"111": {"title": "Test", "summary": "요약"}})
    loaded = load_checkpoint(path)
    assert "111" in loaded
    assert loaded["111"]["title"] == "Test"


def test_checkpoint_missing_file_returns_empty(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    loaded = load_checkpoint(path)
    assert loaded == {}


@patch("fetch_history.summarize")
def test_summarize_stories_skips_checkpointed(mock_summarize):
    mock_summarize.return_value = {"summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요"}
    stories = [
        {"objectID": "111", "title": "Already done", "url": "https://a.com", "points": 200, "created_at": "2024-11-07T00:00:00Z"},
        {"objectID": "222", "title": "New one", "url": "https://b.com", "points": 150, "created_at": "2024-11-19T00:00:00Z"},
    ]
    existing_checkpoint = {"111": {"title": "Already done", "summary": "이미 요약됨"}}

    results = summarize_stories(stories, existing_checkpoint, api_key="fake-key", checkpoint_path=None, delay=0)
    # 111은 스킵, 222만 요약 호출
    mock_summarize.assert_called_once()
    assert "111" in results
    assert "222" in results
    assert results["111"]["summary"] == "이미 요약됨"
    assert results["222"]["summary"] == "요약"


def test_build_history_embed_format():
    story = {
        "title": "Claude AI releases MCP",
        "url": "https://example.com/mcp",
        "points": 347,
        "created_at": "2024-11-15T12:00:00Z",
        "summary": "MCP 프로토콜이 출시되었습니다.",
        "tags": "신기능",
        "reason": "AI 도구 생태계에 큰 변화",
    }
    embed = build_history_embed(story)
    assert embed["title"] == "Claude AI releases MCP"
    assert embed["url"] == "https://example.com/mcp"
    assert embed["color"] == 0xFF6600
    assert "347 points" in embed["description"]
    assert "2024-11-15" in embed["description"]
    assert "MCP 프로토콜이 출시되었습니다." in embed["description"]
    assert embed["author"]["name"] == "Hacker News"


@patch("fetch_history.post_history_to_discord")
@patch("fetch_history.summarize_stories")
@patch("fetch_history.collect_all_hn_stories")
@patch("fetch_history.load_checkpoint", return_value={})
def test_main_full_pipeline(mock_cp, mock_collect, mock_summarize, mock_post):
    mock_collect.return_value = [
        {"objectID": "111", "title": "Test", "url": "https://test.com", "points": 200, "created_at": "2024-11-07T00:00:00Z"},
    ]
    mock_summarize.return_value = {
        "111": {"title": "Test", "url": "https://test.com", "points": 200, "created_at": "2024-11-07T00:00:00Z", "summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요"},
    }

    from fetch_history import main
    main()

    mock_collect.assert_called_once()
    mock_summarize.assert_called_once()
    mock_post.assert_called_once()
