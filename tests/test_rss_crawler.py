import os
import pytest
from unittest.mock import patch, MagicMock
from crawlers.rss_crawler import parse_feed, fetch_rss


def test_parse_github_atom(fixtures_dir):
    path = os.path.join(fixtures_dir, "claude-code-releases.atom")
    with open(path, "r", encoding="utf-8") as f:
        xml = f.read()
    articles = parse_feed(xml, "claude-code")
    assert len(articles) > 0
    first = articles[0]
    assert "title" in first
    assert "url" in first
    assert first["source"] == "claude-code"
    assert first["url"].startswith("http")


def test_parse_aider_atom(fixtures_dir):
    path = os.path.join(fixtures_dir, "aider-releases.atom")
    with open(path, "r", encoding="utf-8") as f:
        xml = f.read()
    articles = parse_feed(xml, "aider")
    assert len(articles) > 0
    assert all(a["source"] == "aider" for a in articles)


def test_empty_feed_returns_empty():
    articles = parse_feed("", "test")
    assert articles == []


def test_malformed_feed_no_crash():
    articles = parse_feed("<not><valid>xml</garbage>", "test")
    assert articles == []


@patch("crawlers.rss_crawler.requests.get")
def test_fetch_rss_success(mock_get):
    with open(
        os.path.join(os.path.dirname(__file__), "fixtures", "aider-releases.atom"),
        "r", encoding="utf-8",
    ) as f:
        xml = f.read()
    mock_get.return_value = MagicMock(status_code=200, text=xml)
    articles = fetch_rss("https://example.com/feed.atom", "aider")
    assert len(articles) > 0


@patch("crawlers.rss_crawler.requests.get")
def test_fetch_rss_network_error(mock_get):
    mock_get.side_effect = ConnectionError("no network")
    articles = fetch_rss("https://example.com/feed.atom", "test")
    assert articles == []
