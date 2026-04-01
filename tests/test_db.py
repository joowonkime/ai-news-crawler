import sqlite3
from db import init_db, insert_article, get_unposted, mark_posted


def test_init_creates_table(tmp_db):
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
    ).fetchall()
    conn.close()
    assert len(tables) == 1


def test_insert_article(tmp_db):
    init_db(tmp_db)
    article = {
        "source": "claude-code",
        "title": "v1.0 Release",
        "url": "https://example.com/1",
        "content": "New release content",
        "published_at": "2026-04-01",
    }
    inserted = insert_article(tmp_db, article)
    assert inserted is True

    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT * FROM articles WHERE url=?", (article["url"],)).fetchone()
    conn.close()
    assert row is not None
    assert row[1] == "claude-code"  # source
    assert row[2] == "v1.0 Release"  # title


def test_duplicate_url_rejected(tmp_db):
    init_db(tmp_db)
    article = {
        "source": "claude-code",
        "title": "v1.0 Release",
        "url": "https://example.com/dup",
        "content": "content",
        "published_at": "2026-04-01",
    }
    first = insert_article(tmp_db, article)
    second = insert_article(tmp_db, article)
    assert first is True
    assert second is False

    conn = sqlite3.connect(tmp_db)
    count = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE url=?", (article["url"],)
    ).fetchone()[0]
    conn.close()
    assert count == 1


def test_get_unposted(tmp_db):
    init_db(tmp_db)
    for i in range(3):
        insert_article(tmp_db, {
            "source": "test",
            "title": f"Article {i}",
            "url": f"https://example.com/{i}",
            "content": "c",
            "published_at": "2026-04-01",
        })

    unposted = get_unposted(tmp_db)
    assert len(unposted) == 3


def test_mark_posted(tmp_db):
    init_db(tmp_db)
    insert_article(tmp_db, {
        "source": "test",
        "title": "Article",
        "url": "https://example.com/mark",
        "content": "c",
        "published_at": "2026-04-01",
    })

    unposted = get_unposted(tmp_db)
    assert len(unposted) == 1

    mark_posted(tmp_db, unposted[0]["id"])
    unposted_after = get_unposted(tmp_db)
    assert len(unposted_after) == 0
