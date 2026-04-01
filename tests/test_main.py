from unittest.mock import patch, MagicMock
from main import run_pipeline


def _fake_articles(source, n=2):
    return [
        {
            "source": source,
            "title": f"{source} article {i}",
            "url": f"https://example.com/{source}/{i}",
            "content": f"Content for {source} {i}",
            "published_at": "2026-04-01",
        }
        for i in range(n)
    ]


@patch("main.send_to_discord", return_value=True)
@patch("main.summarize", return_value={"summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요한 업데이트"})
@patch("main.fetch_threads", return_value=[])
@patch("main.fetch_html", return_value="")
@patch("main.fetch_rss", return_value=[])
def test_pipeline_no_new_articles(
    mock_rss, mock_html_fetch, mock_threads, mock_summarize, mock_discord, tmp_db
):
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    mock_discord.assert_not_called()


@patch("main.send_to_discord", return_value=True)
@patch("main.summarize", return_value={"summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요한 업데이트"})
@patch("main.fetch_threads", return_value=[])
@patch("main.fetch_html", return_value="")
@patch("main.fetch_rss")
def test_pipeline_new_articles_posted(
    mock_rss, mock_html_fetch, mock_threads, mock_summarize, mock_discord, tmp_db
):
    mock_rss.return_value = _fake_articles("claude-code", 2)
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    assert mock_discord.call_count == 2


@patch("main.send_to_discord", return_value=True)
@patch("main.summarize", return_value=None)
@patch("main.fetch_threads", return_value=[])
@patch("main.fetch_html", return_value="")
@patch("main.fetch_rss")
def test_pipeline_gemini_fails_skips_post(
    mock_rss, mock_html_fetch, mock_threads, mock_summarize, mock_discord, tmp_db
):
    mock_rss.return_value = _fake_articles("claude-code", 1)
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    mock_discord.assert_not_called()


@patch("main.send_to_discord", return_value=True)
@patch("main.summarize")
@patch("main.fetch_threads", return_value=[])
@patch("main.fetch_html", return_value="")
@patch("main.fetch_rss")
def test_pipeline_retries_unsummarized_next_run(
    mock_rss, mock_html_fetch, mock_threads, mock_summarize, mock_discord, tmp_db
):
    mock_rss.return_value = _fake_articles("claude-code", 1)
    # First run: summarize fails → skip
    mock_summarize.return_value = None
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    mock_discord.assert_not_called()

    # Second run: summarize succeeds → post
    mock_summarize.return_value = {"summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요한 업데이트"}
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    assert mock_discord.call_count == 1


@patch("main.send_to_discord", return_value=True)
@patch("main.summarize", return_value={"summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요한 업데이트"})
@patch("main.fetch_threads", return_value=[])
@patch("main.fetch_html", return_value="")
@patch("main.fetch_rss")
def test_pipeline_duplicates_not_reposted(
    mock_rss, mock_html_fetch, mock_threads, mock_summarize, mock_discord, tmp_db
):
    mock_rss.return_value = _fake_articles("claude-code", 1)
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    assert mock_discord.call_count == 1

    mock_discord.reset_mock()
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    mock_discord.assert_not_called()


@patch("main.send_to_discord", return_value=True)
@patch("main.summarize", return_value={"summary": "요약", "tags": "신기능", "importance": 8, "reason": "중요한 업데이트"})
@patch("main.fetch_threads", return_value=[])
@patch("main.fetch_html", return_value="")
@patch("main.fetch_rss", return_value=[])
def test_single_source_flag(
    mock_rss, mock_html_fetch, mock_threads, mock_summarize, mock_discord, tmp_db
):
    run_pipeline(db_path=tmp_db, sources=["claude-code"])
    mock_rss.assert_called_once()
    mock_threads.assert_not_called()
