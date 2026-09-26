from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord
from core.utils import compact_join, normalize_whitespace


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean records, keep the first valid record per ID, and sort newest first.

    Dates use UTC and are exported as YYYY-MM-DD strings. Records without an
    ID, title, or valid publication date are skipped; missing summaries are kept.
    """
    run_timestamp = pd.to_datetime(run_date, utc=True, errors="raise")
    if pd.isna(run_timestamp):
        raise ValueError("run_date must be a valid date.")

    columns = [field.name for field in fields(PaperRecord)] + [
        "age_days", "authors_joined", "categories_joined", "summary_chars",
        "text_for_embedding",
    ]
    cleaned_records = []
    for record in records:
        row = asdict(record)
        for key, value in row.items():
            if key not in {"authors", "categories"}:
                row[key] = normalize_whitespace(value or "")
        for key in ("authors", "categories"):
            row[key] = [
                text for value in (row[key] or [])
                if (text := normalize_whitespace(value or ""))
            ]

        published = pd.to_datetime(row["published"], utc=True, errors="coerce")
        if not row["paper_id"] or not row["title"] or pd.isna(published):
            continue
        updated = pd.to_datetime(row["updated"], utc=True, errors="coerce")
        row["age_days"] = (run_timestamp - published).days
        row["published"] = published.strftime("%Y-%m-%d")
        row["updated"] = updated.strftime("%Y-%m-%d") if pd.notna(updated) else ""
        row["authors_joined"] = compact_join(row["authors"])
        row["categories_joined"] = compact_join(row["categories"])
        row["summary_chars"] = len(row["summary"])
        row["text_for_embedding"] = "\n".join([
            f"Title: {row['title']}",
            f"Authors: {row['authors_joined']}",
            f"Published: {row['published']}",
            f"Categories: {row['categories_joined']}",
            f"Summary: {row['summary']}",
        ])
        cleaned_records.append(row)

    df = pd.DataFrame(cleaned_records, columns=columns)
    df = df.astype({"age_days": "int64", "summary_chars": "int64"})
    return (
        df.drop_duplicates(subset="paper_id", keep="first")
        .sort_values("published", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
