from unittest.mock import patch, MagicMock
from discord_poster import build_embed, send_to_discord


def _make_article(**overrides):
    base = {
        "id": 1,
        "source": "claude-code",
        "title": "v1.0 Release",
        "url": "https://example.com/1",
        "content": "content",
        "summary": "한국어 요약입니다.",
        "tags": '["신기능"]',
        "published_at": "2026-04-01",
    }
    base.update(overrides)
    return base


def test_build_embed_structure():
    embed = build_embed(_make_article())
    assert embed["title"] == "v1.0 Release"
    assert embed["url"] == "https://example.com/1"
    assert embed["color"] == 0x5865F2
    assert "한국어 요약" in embed["description"]
    assert embed["author"]["name"] == "Claude Code"
    assert embed["footer"]["text"] == "2026-04-01"


def test_build_embed_truncates_long_summary():
    long_summary = "가" * 2100
    embed = build_embed(_make_article(summary=long_summary))
    assert len(embed["description"]) <= 2048


def test_build_embed_no_summary_uses_content():
    embed = build_embed(_make_article(summary=None))
    assert "content" in embed["description"]


def test_build_embed_with_tags():
    embed = build_embed(_make_article(tags='["신기능", "성능"]'))
    assert "신기능" in embed["description"]
    assert "성능" in embed["description"]


@patch("discord_poster.requests.post")
def test_send_calls_webhook(mock_post):
    mock_post.return_value = MagicMock(status_code=204)
    article = _make_article()
    result = send_to_discord("https://webhook.url", article)
    assert result is True
    mock_post.assert_called_once()
    call_json = mock_post.call_args[1]["json"]
    assert "embeds" in call_json


@patch("discord_poster.requests.post")
def test_send_retries_on_rate_limit(mock_post):
    rate_resp = MagicMock(status_code=429, json=lambda: {"retry_after": 0.01})
    ok_resp = MagicMock(status_code=204)
    mock_post.side_effect = [rate_resp, ok_resp]
    result = send_to_discord("https://webhook.url", _make_article())
    assert result is True
    assert mock_post.call_count == 2
