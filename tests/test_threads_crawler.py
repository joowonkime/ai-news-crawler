import os
from crawlers.threads_crawler import parse_threads_html


def test_parse_threads_html(fixtures_dir):
    path = os.path.join(fixtures_dir, "threads-choi-openai.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    posts = parse_threads_html(html)
    assert len(posts) > 0


def test_extracts_post_url_and_text(fixtures_dir):
    path = os.path.join(fixtures_dir, "threads-choi-openai.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    posts = parse_threads_html(html)
    first = posts[0]
    assert first["source"] == "threads-choi"
    assert "threads.com" in first["url"]
    assert "/post/" in first["url"]
    assert first["title"]
    assert first["published_at"]


def test_empty_html_returns_empty():
    posts = parse_threads_html("<html><body></body></html>")
    assert posts == []
