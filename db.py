import sqlite3


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            content TEXT,
            summary TEXT,
            tags TEXT,
            importance INTEGER DEFAULT 0,
            published_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            posted_to_discord INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def insert_article(db_path: str, article: dict) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO articles (source, title, url, content, published_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                article["source"],
                article["title"],
                article["url"],
                article.get("content", ""),
                article.get("published_at", ""),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_unposted(db_path: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM articles WHERE posted_to_discord = 0 ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_summary(db_path: str, article_id: int, summary: str, tags: str, importance: int = 0):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE articles SET summary = ?, tags = ?, importance = ? WHERE id = ?",
        (summary, tags, importance, article_id),
    )
    conn.commit()
    conn.close()


def mark_posted(db_path: str, article_id: int):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE articles SET posted_to_discord = 1 WHERE id = ?", (article_id,)
    )
    conn.commit()
    conn.close()
