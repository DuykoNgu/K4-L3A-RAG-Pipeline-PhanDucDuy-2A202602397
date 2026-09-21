"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
REQUEST_TIMEOUT_SECONDS = 30

LEGAL_SOURCES = {
    "ielts-academic-writing-sample-tasks.pdf": (
        "https://ielts.org/cdn/Sample-tests/"
        "ielts-academic-writing-sample-tasks-2023.pdf"
    ),
    "ielts-general-training-writing-sample-tasks.pdf": (
        "https://ielts.org/cdn/Sample-tests/"
        "ielts-general-training-writing-sample-tasks-2023.pdf"
    ),
    "ielts-writing-band-descriptors.pdf": (
        "https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf"
    ),
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    for filename, url in LEGAL_SOURCES.items():
        destination = DATA_DIR / filename
        if destination.exists() and destination.stat().st_size > 0:
            print(f"Skipped existing: {destination}")
            continue

        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        destination.write_bytes(response.content)
        print(f"Downloaded: {destination}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
