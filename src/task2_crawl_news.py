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
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://ielts.org/take-a-test/preparation-resources/writing-test-resources",
    "https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail",
    "https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing",
    "https://ielts.org/organisations/ielts-for-organisations/test-types/ielts-academic-test",
    "https://ielts.org/organisations/ielts-for-organisations/understanding-ielts-scoring/resources-for-setting-your-ielts-scores",
]


async def crawl_article(url: str) -> dict:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    if not result.success:
        error = getattr(result, "error_message", "unknown crawler error")
        raise RuntimeError(f"crawl failed: {error}")

    metadata = result.metadata or {}
    title = metadata.get("title") or urlparse(url).path.rsplit("/", 1)[-1]
    markdown = getattr(result, "markdown", "")
    markdown = getattr(markdown, "raw_markdown", markdown)
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("crawler returned empty Markdown")

    return {
        "url": url,
        "title": title.strip(),
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown.strip(),
    }


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
