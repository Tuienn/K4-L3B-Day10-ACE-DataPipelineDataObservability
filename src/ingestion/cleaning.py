from __future__ import annotations

from datetime import datetime
import re

import pandas as pd

from ingestion.crossref import PaperRecord


def _clean_str(val: str | None) -> str:
    """Loại bỏ khoảng trắng thừa và ký tự rỗng."""
    if not val:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", str(val))
    return " ".join(cleaned.split())


def format_text_for_embedding(
    title: str,
    authors_joined: str,
    published: str,
    categories_joined: str,
    summary: str,
) -> str:
    """Ghép nối các trường thành một đoạn ngữ cảnh hoàn chỉnh text_for_embedding:

    Title: <Tiêu đề bài báo>
    Authors: <Danh sách tác giả>
    Published: <Ngày xuất bản>
    Categories: <Lĩnh vực chuyên môn>

    Summary: <Tóm tắt nội dung>
    """
    return (
        f"Title: {title}\n"
        f"Authors: {authors_joined}\n"
        f"Published: {published}\n"
        f"Categories: {categories_joined}\n\n"
        f"Summary: {summary}"
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thành dataframe sẵn sàng để embed.

    1. Normalize title, summary, authors, categories, loại bỏ khoảng trắng thừa.
    2. Parse published/updated date.
    3. Tính toán tuổi đời dữ liệu: age_days = (run_date - published).days.
    4. Tạo các cột helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Khử trùng lặp theo khóa duy nhất paper_id và lọc bỏ dòng không hợp lệ.
    6. Sắp xếp theo ngày xuất bản mới nhất trước (stable sort) và return.
    """
    run_date_obj = run_date.date() if isinstance(run_date, datetime) else run_date

    columns = [
        "paper_id",
        "title",
        "summary",
        "authors",
        "authors_joined",
        "categories",
        "categories_joined",
        "primary_category",
        "published",
        "updated",
        "abs_url",
        "pdf_url",
        "comment",
        "age_days",
        "summary_chars",
        "text_for_embedding",
    ]

    rows: list[dict] = []
    for r in records:
        paper_id = _clean_str(r.paper_id)
        if not paper_id:
            continue

        title = _clean_str(r.title)
        if not title:
            continue

        summary = _clean_str(r.summary)

        # Chuẩn hóa authors
        authors = [_clean_str(a) for a in (r.authors or []) if _clean_str(a)]
        authors_joined = ", ".join(authors)

        # Chuẩn hóa categories
        categories = [_clean_str(c) for c in (r.categories or []) if _clean_str(c)]
        categories_joined = ", ".join(categories)
        primary_category = _clean_str(r.primary_category) or (categories[0] if categories else "")

        published = _clean_str(r.published)
        updated = _clean_str(r.updated) or published

        # Tính toán age_days
        age_days = 0
        if published:
            try:
                pub_date = datetime.strptime(published[:10], "%Y-%m-%d").date()
                age_days = max(0, (run_date_obj - pub_date).days)
            except Exception:
                age_days = 0

        summary_chars = len(summary)

        text_for_embedding = format_text_for_embedding(
            title=title,
            authors_joined=authors_joined,
            published=published,
            categories_joined=categories_joined,
            summary=summary,
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "authors_joined": authors_joined,
                "categories": categories,
                "categories_joined": categories_joined,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": _clean_str(r.abs_url),
                "pdf_url": _clean_str(r.pdf_url),
                "comment": _clean_str(r.comment),
                "age_days": age_days,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
            }
        )

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows, columns=columns)
    df = df.astype({"age_days": "int64", "summary_chars": "int64"})
    # Khử trùng lặp bản ghi theo khóa duy nhất paper_id và sắp xếp mới nhất
    return (
        df.drop_duplicates(subset=["paper_id"], keep="first")
        .sort_values(by="published", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
