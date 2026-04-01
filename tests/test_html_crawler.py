import os
import pytest
from unittest.mock import patch, MagicMock
from crawlers.html_crawler import (
    parse_anthropic,
    parse_cursor,
    parse_windsurf,
    parse_devin,
    fetch_html,
)


def test_parse_anthropic(fixtures_dir):
    path = os.path.join(fixtures_dir, "anthropic-news.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    articles = parse_anthropic(html)
    assert len(articles) > 0
    first = articles[0]
    assert first["source"] == "anthropic-blog"
    assert first["title"]
    assert first["url"].startswith("https://www.anthropic.com/news/")


def test_parse_cursor(fixtures_dir):
    path = os.path.join(fixtures_dir, "cursor-changelog.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    articles = parse_cursor(html)
    assert len(articles) > 0
    first = articles[0]
    assert first["source"] == "cursor"
    assert first["title"]
    assert first["url"].startswith("https://cursor.com/changelog/")
    assert first["published_at"]


def test_parse_windsurf(fixtures_dir):
    path = os.path.join(fixtures_dir, "windsurf-changelog.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    articles = parse_windsurf(html)
    assert len(articles) > 0
    first = articles[0]
    assert first["source"] == "windsurf-changelog"
    assert first["title"]
    assert first["published_at"]


def test_parse_devin(fixtures_dir):
    path = os.path.join(fixtures_dir, "devin-release-notes.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    articles = parse_devin(html)
    assert len(articles) > 0
    first = articles[0]
    assert first["source"] == "devin"
    assert first["title"]
    assert first["published_at"]


def test_network_error_returns_empty():
    with patch("crawlers.html_crawler.requests.get", side_effect=ConnectionError):
        result = fetch_html("https://example.com", "test")
    assert result == ""


def test_changed_html_structure_no_crash():
    articles = parse_anthropic("<html><body><p>Nothing here</p></body></html>")
    assert articles == []
