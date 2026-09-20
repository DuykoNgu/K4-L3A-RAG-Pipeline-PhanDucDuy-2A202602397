"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://ielts.org/take-a-test/preparation-resources/writing-test-resources",
    "https://ielts.org/news-and-insights/ielts-writing-band-descriptors-and-key-assessment-criteria",
    "https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing",
    "https://ielts.org/organisations/ielts-for-organisations/test-types/ielts-academic-test",
    "https://ielts.org/organisations/ielts-for-organisations/understanding-ielts-scoring/resources-for-setting-your-ielts-scores",
]


class _PageTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._ignored_depth = 0
        self._main_depth = 0
        self._has_main = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
        if tag == "main" or attributes.get("role") == "main":
            if not self._has_main:
                self.parts = []
            self._main_depth += 1
            self._has_main = True
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1
        if tag == "main" and self._main_depth:
            self._main_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text or self._ignored_depth or (self._has_main and not self._main_depth):
            return
        if self._in_title:
            self.title = text
        self.parts.append(text)


async def crawl_article(url: str) -> dict:
    def fetch() -> dict:
        response = requests.get(
            url,
            timeout=45,
            headers={"User-Agent": "Mozilla/5.0 (educational RAG corpus collector)"},
        )
        response.raise_for_status()
        parser = _PageTextExtractor()
        parser.feed(response.text)
        content = "\n\n".join(parser.parts)
        if len(content) < 200:
            raise ValueError(f"Extracted content is too short: {url}")
        return {
            "url": url,
            "title": parser.title or url,
            "date_crawled": datetime.now(timezone.utc).isoformat(),
            "content_markdown": content,
        }

    return await asyncio.to_thread(fetch)


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
