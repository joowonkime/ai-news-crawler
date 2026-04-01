import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def fetch_html(url: str, source_key: str) -> str:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error("Failed to fetch %s (%s): %s", source_key, url, e)
        return ""


def parse_anthropic(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    links = soup.find_all("a", href=True)
    for link in links:
        href = link.get("href", "")
        if not href.startswith("/news/") or len(href) <= 6:
            continue
        h3 = link.find(["h3", "h2", "h4"])
        if not h3:
            continue
        title = h3.get_text().strip()
        url = f"https://www.anthropic.com{href}"
        spans = link.find_all("span")
        date_text = ""
        for span in spans:
            text = span.get_text().strip()
            if any(m in text for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                date_text = text
                break

        articles.append({
            "source": "anthropic-blog",
            "title": title,
            "url": url,
            "content": "",
            "published_at": date_text,
        })
    return articles


def parse_cursor(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for article in soup.find_all("article"):
        h1 = article.find("h1")
        time_el = article.find("time")
        link = article.find("a", href=lambda h: h and "/changelog/" in h)
        if not h1:
            continue
        title = h1.get_text().strip()
        url = f"https://cursor.com{link['href']}" if link else ""
        date = time_el.get("datetime", time_el.get_text().strip()) if time_el else ""
        articles.append({
            "source": "cursor",
            "title": title,
            "url": url,
            "content": "",
            "published_at": date,
        })
    return articles


def parse_windsurf(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    layouts = soup.find_all("div", attrs={"aria-label": "changelog-layout"})
    for layout in layouts:
        header = layout.find("header")
        article = layout.find("article")
        if not article:
            continue
        h1 = article.find("h1")
        if not h1:
            continue
        title = h1.get_text().strip()
        date_text = ""
        version = ""
        if header:
            divs = header.find_all("div")
            if len(divs) >= 2:
                version = divs[0].get_text().strip()
                date_text = divs[1].get_text().strip()

        content_parts = []
        for li in article.find_all("li"):
            content_parts.append(li.get_text().strip())

        articles.append({
            "source": "windsurf-changelog",
            "title": f"{title} ({version})" if version else title,
            "url": f"https://windsurf.com/changelog#{h1.get('id', '')}",
            "content": "\n".join(content_parts[:10]),
            "published_at": date_text,
        })
    return articles


def parse_devin(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    labels = soup.find_all("div", attrs={"data-component-part": "update-label"})
    contents = soup.find_all("div", attrs={"data-component-part": "update-content"})
    for label, content in zip(labels, contents):
        date_text = label.get_text().strip()
        features = content.find_all("span", recursive=True)
        feature_names = []
        for span in features:
            text = span.get_text().strip()
            if text and len(text) < 100:
                feature_names.append(text)

        title = feature_names[0] if feature_names else date_text
        content_text = "\n".join(feature_names[:10])

        slug = date_text.lower().replace(" ", "-").replace(",", "")
        articles.append({
            "source": "devin",
            "title": title,
            "url": f"https://docs.devin.ai/release-notes/overview#{slug}",
            "content": content_text,
            "published_at": date_text,
        })
    return articles
