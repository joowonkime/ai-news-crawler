import json
from unittest.mock import patch, MagicMock
from fetch_history import search_hn, collect_all_hn_stories, KEYWORDS

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
