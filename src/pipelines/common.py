"""Shared orchestration helpers; student-owned data transformations stay external."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from core.config import Settings
from core.utils import write_csv, write_json
from observability.quality import build_freshness_report, run_data_quality_checks


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def experiment_config(settings: Settings) -> dict:
    # Never serialize Settings: it contains API credentials.
    return {"evaluation_version": 2, **{name: getattr(settings, name) for name in (
        "llm_provider", "model_name", "embedding_model", "top_k",
        "freshness_threshold_days",
    )}}


def save_frame(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    if df.empty:
        raise ValueError("Cannot index an empty dataset.")
    required = {"paper_id", "title", "published", "summary", "authors_joined",
                "categories_joined", "abs_url", "pdf_url", "text_for_embedding", "age_days"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Clean dataframe contract missing columns: {sorted(missing)}")
    write_csv(df, csv_path)
    write_json(json_path, json.loads(df.to_json(orient="records", date_format="iso")))


def observe(df: pd.DataFrame, settings: Settings, stage: str) -> tuple[dict, dict]:
    quality = run_data_quality_checks(df, settings, stage)
    freshness_path = (settings.paths.freshness_report if stage == "baseline"
                      else settings.paths.quality_dir / f"{stage}_freshness_report.json")
    freshness = build_freshness_report(df, settings, freshness_path)
    write_json(settings.paths.quality_dir / f"{stage}_quality_report.json", quality)
    write_json(freshness_path, freshness)
    print(f"[{stage}] quality={quality.get('success')}, fresh={freshness.get('is_fresh')}")
    return quality, freshness


def require_healthy(quality: dict, freshness: dict, stage: str) -> None:
    if not quality.get("success") or not freshness.get("is_fresh"):
        raise ValueError(f"{stage} quality/freshness gate failed; inspect data/quality/ before indexing.")


def validate_test_set(test_set: list, df: pd.DataFrame) -> None:
    if not isinstance(test_set, list) or not test_set:
        raise ValueError("Evaluation set must be a non-empty list.")
    ids = set(df["paper_id"])
    question_ids = set()
    for item in test_set:
        for field in ("id", "question_type", "question", "ground_truth", "ground_truth_doc_ids"):
            if field not in item or not item[field]:
                raise ValueError(f"Evaluation item missing {field}.")
        if item["id"] in question_ids:
            raise ValueError("Duplicate evaluation question ID.")
        question_ids.add(item["id"])
        if not isinstance(item["ground_truth_doc_ids"], list) or not set(item["ground_truth_doc_ids"]) <= ids:
            raise ValueError("Evaluation references absent papers; rebuild baseline with REFRESH_TEST_SET=1.")
