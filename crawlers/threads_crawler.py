import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_threads_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    seen_urls = set()

    divs = soup.find_all("div", attrs={"data-pressable-container": True})
    for div in divs:
        time_el = div.find("time")
        if not time_el:
            continue

        links = div.find_all("a", href=True)
        post_link = None
        for link in links:
            href = link.get("href", "")
            if "/post/" in href and "/media" not in href:
                post_link = href
                break
        if not post_link:
            continue

        url = f"https://www.threads.com{post_link}"
        if url in seen_urls:
            continue
        seen_urls.add(url)

        all_text = div.get_text(separator="|||")
        parts = [p.strip() for p in all_text.split("|||") if p.strip()]
        meaningful = [p for p in parts if len(p) > 10 and p != "choi.openai"]

        text = meaningful[0] if meaningful else ""
        if not text:
            continue

        title = text[:100] + ("..." if len(text) > 100 else "")

        posts.append({
            "source": "threads-choi",
            "title": title,
            "url": url,
            "content": text,
            "published_at": time_el.get("datetime", ""),
        })

    return posts


def fetch_threads(url: str, max_posts: int = 20) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
        import time

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            time.sleep(5)

            for _ in range(5):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(2)

            html = page.content()
            browser.close()

        posts = parse_threads_html(html)
        return posts[:max_posts]

    except Exception as e:
        logger.error("Failed to fetch Threads: %s", e)
        return []
