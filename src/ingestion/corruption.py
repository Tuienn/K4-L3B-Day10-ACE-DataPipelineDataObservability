from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json
from ingestion.cleaning import format_text_for_embedding


DROP_LATEST_RATIO = 0.20
MUTATION_RATIO = 0.10
NOISE_MARKER = "[CORRUPTED_NOISE] ###@@@ xqzv-9917"


def _row_change(
    df: pd.DataFrame,
    row_index: int,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a JSON-serializable audit entry for one affected row."""
    return {
        "row_index": int(row_index),
        "paper_id": str(df.at[row_index, "paper_id"]),
        "before": before,
        "after": after,
    }


def _operation_log(operation: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "operation": operation,
        "affected_count": len(rows),
        "rows": rows,
    }


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Inject six deterministic corruption scenarios and write an audit log.

    The input dataframe is never modified in place. Row selection is
    deterministic so repeated runs on the same clean snapshot produce the
    same corrupted dataset and the same affected paper IDs.
    """
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "categories_joined",
        "published",
        "age_days",
        "summary_chars",
        "text_for_embedding",
    }
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Missing columns required for corruption: {missing_columns}")
    if len(df) < 6:
        raise ValueError("At least 6 clean rows are required to inject all corruption scenarios.")

    clean_df = df.copy(deep=True).reset_index(drop=True)
    operations: list[dict[str, Any]] = []

    # 1. Drop approximately 20% of the newest records.
    drop_count = max(1, round(len(clean_df) * DROP_LATEST_RATIO))
    published_dates = pd.to_datetime(clean_df["published"], errors="coerce", utc=True)
    latest_indices = list(
        published_dates.sort_values(ascending=False, na_position="last")
        .index[:drop_count]
    )
    dropped_rows = [
        _row_change(
            clean_df,
            row_index,
            before={"published": str(clean_df.at[row_index, "published"])},
            after=None,
        )
        for row_index in latest_indices
    ]
    operations.append(_operation_log("drop_latest_records", dropped_rows))
    corrupted = clean_df.drop(index=latest_indices).reset_index(drop=True)

    mutation_count = min(
        len(corrupted),
        max(1, round(len(clean_df) * MUTATION_RATIO)),
    )
    row_count = len(corrupted)
    cursor = 0

    def next_indices(count: int = mutation_count) -> list[int]:
        nonlocal cursor
        selected = [((cursor + offset) % row_count) for offset in range(count)]
        cursor += count
        return selected

    # 2. Blank summaries.
    blank_changes: list[dict[str, Any]] = []
    for row_index in next_indices():
        before = str(corrupted.at[row_index, "summary"])
        corrupted.at[row_index, "summary"] = ""
        blank_changes.append(
            _row_change(
                corrupted,
                row_index,
                before={"summary": before},
                after={"summary": ""},
            )
        )
    operations.append(_operation_log("blank_summary", blank_changes))

    # 3. Inject a deterministic noise marker into summaries.
    noise_changes: list[dict[str, Any]] = []
    for row_index in next_indices():
        before = str(corrupted.at[row_index, "summary"])
        after = f"{before} {NOISE_MARKER}".strip()
        corrupted.at[row_index, "summary"] = after
        noise_changes.append(
            _row_change(
                corrupted,
                row_index,
                before={"summary": before},
                after={"summary": after},
            )
        )
    operations.append(_operation_log("inject_noise", noise_changes))

    # 4. Truncate titles to fewer than eight characters.
    title_changes: list[dict[str, Any]] = []
    for row_index in next_indices():
        before = str(corrupted.at[row_index, "title"])
        after = before[:7]
        corrupted.at[row_index, "title"] = after
        title_changes.append(
            _row_change(
                corrupted,
                row_index,
                before={"title": before},
                after={"title": after},
            )
        )
    operations.append(_operation_log("truncate_title", title_changes))

    # 5. Move publication dates back by 365 days and keep age_days aligned.
    # Corrupt enough rows to make the final stale ratio exceed the 25% SLA.
    final_row_count = row_count + mutation_count
    stale_count = min(row_count, int(final_row_count * 0.25) + 1)
    stale_changes: list[dict[str, Any]] = []
    for row_index in next_indices(stale_count):
        before_published = str(corrupted.at[row_index, "published"])
        before_age = int(corrupted.at[row_index, "age_days"])
        parsed_date = pd.to_datetime(before_published, errors="coerce")
        if pd.isna(parsed_date):
            raise ValueError(
                f"Cannot inject stale_date for paper {corrupted.at[row_index, 'paper_id']}: "
                f"invalid published value {before_published!r}."
            )
        after_published = (parsed_date - pd.Timedelta(days=365)).date().isoformat()
        after_age = before_age + 365
        corrupted.at[row_index, "published"] = after_published
        corrupted.at[row_index, "age_days"] = after_age
        stale_changes.append(
            _row_change(
                corrupted,
                row_index,
                before={"published": before_published, "age_days": before_age},
                after={"published": after_published, "age_days": after_age},
            )
        )
    operations.append(_operation_log("stale_date", stale_changes))

    # 6. Append exact copies of selected rows to create duplicate paper IDs.
    duplicate_source_indices = list(range(max(0, row_count - mutation_count), row_count))
    duplicates = corrupted.loc[duplicate_source_indices].copy(deep=True)
    duplicate_changes: list[dict[str, Any]] = []
    first_duplicate_index = len(corrupted)
    for offset, source_index in enumerate(duplicate_source_indices):
        duplicate_changes.append(
            {
                "source_row_index": int(source_index),
                "duplicate_row_index": first_duplicate_index + offset,
                "paper_id": str(corrupted.at[source_index, "paper_id"]),
            }
        )
    corrupted = pd.concat([corrupted, duplicates], ignore_index=True)
    operations.append(_operation_log("duplicate_rows", duplicate_changes))

    # Rebuild every derived text field after corruption so the vector index
    # receives the corrupted values rather than stale clean text.
    corrupted["summary_chars"] = corrupted["summary"].fillna("").astype(str).str.len()
    corrupted["text_for_embedding"] = corrupted.apply(
        lambda row: format_text_for_embedding(
            title=str(row["title"]),
            authors_joined=str(row["authors_joined"]),
            published=str(row["published"]),
            categories_joined=str(row["categories_joined"]),
            summary=str(row["summary"]),
        ),
        axis=1,
    )
    corrupted["age_days"] = pd.to_numeric(corrupted["age_days"], errors="raise").astype("int64")
    corrupted["summary_chars"] = corrupted["summary_chars"].astype("int64")

    log_payload = {
        "input_rows": len(clean_df),
        "output_rows": len(corrupted),
        "operations": operations,
    }
    write_json(Path(output_log_path), log_payload)
    return corrupted
