"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path

from markitdown import MarkItDown

from .task1_collect_legal_docs import LEGAL_SOURCES


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
LEGAL_TITLES = {
    "ielts-academic-writing-sample-tasks.pdf": "IELTS Academic Writing Sample Tasks",
    "ielts-general-training-writing-sample-tasks.pdf": (
        "IELTS General Training Writing Sample Tasks"
    ),
    "ielts-writing-band-descriptors.pdf": "IELTS Writing Band Descriptors",
}
NEWS_FOOTER_MARKERS = (
    "About us",
    "Which test do I need?",
    "Learn about the other sections of the test",
    "### Preparation resources",
    "### Additional resources",
)


def convert_legal_docs() -> None:
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue

        result = converter.convert(str(path))
        content = result.text_content.strip()
        if not content:
            print(f"Skipped empty conversion: {path}")
            continue

        title = LEGAL_TITLES.get(path.name, path.stem.replace("-", " ").title())
        source_url = LEGAL_SOURCES.get(path.name, "")
        header = (
            f"# {title}\n\n"
            f"**Source:** {source_url}\n\n"
            f"**Document:** {path.name}\n\n"
            "---\n\n"
        )
        output = output_dir / f"{path.stem}.md"
        output.write_text(header + content + "\n", encoding="utf-8")
        print(f"Converted: {output}")


def convert_news_articles() -> None:
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        title = str(data.get("title", "")).strip()
        source_url = str(data.get("url", "")).strip()
        crawled_at = str(data.get("date_crawled", "")).strip()
        raw_content = str(data.get("content_markdown", "")).strip()
        content = clean_news_content(raw_content, title)

        if not all((title, source_url, crawled_at, content)):
            print(f"Skipped incomplete article: {path}")
            continue

        header = (
            f"# {title}\n\n"
            f"**Source:** {source_url}\n\n"
            f"**Crawled:** {crawled_at}\n\n"
            "---\n\n"
        )
        output = output_dir / f"{path.stem}.md"
        output.write_text(header + content + "\n", encoding="utf-8")
        print(f"Converted: {output}")


def clean_news_content(content: str, title: str) -> str:
    """Remove repeated site navigation and footer boilerplate."""
    lines = [line.strip() for line in content.replace("\r\n", "\n").split("\n")]
    heading_positions = [
        index for index, line in enumerate(lines) if line.startswith("# ")
    ]
    title_positions = [index for index, line in enumerate(lines) if line == title]
    start = heading_positions[0] if heading_positions else (
        title_positions[-1] if title_positions else 0
    )
    relevant_lines = lines[start + 1 :] if heading_positions else lines[start:]

    while relevant_lines and relevant_lines[0] == "* * *":
        relevant_lines.pop(0)

    jump_index = next(
        (
            index
            for index, line in enumerate(relevant_lines)
            if line == "Jump to Section"
        ),
        None,
    )
    if jump_index is not None:
        first_section = next(
            (
                index
                for index, line in enumerate(
                    relevant_lines[jump_index + 1 :], jump_index + 1
                )
                if line.startswith("#")
            ),
            None,
        )
        if first_section is not None:
            relevant_lines = relevant_lines[:jump_index] + relevant_lines[first_section:]

    for index, line in enumerate(relevant_lines):
        is_footer_image = line.startswith("[![")
        has_footer_marker = any(
            marker in line for marker in NEWS_FOOTER_MARKERS
        )
        if index > 0 and (is_footer_image or has_footer_marker):
            relevant_lines = relevant_lines[:index]
            break

    return "\n".join(relevant_lines).strip()


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
