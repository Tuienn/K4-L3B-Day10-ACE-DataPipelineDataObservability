from __future__ import annotations

import json
from typing import Any

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def run_phase1_pipeline(settings: Settings) -> dict[str, Any]:
    """Run step 6: ingest -> clean -> index -> test set -> evaluate -> quality -> report.

    Reuse the existing student module contracts. The reporting module must be
    implemented by its owner before this pipeline can finish end-to-end.
    """
    require_llm_credentials(settings)
    paths = settings.paths
    run_date = now_utc()

    print("[baseline] Loading raw records")
    if settings.refresh_source or not paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(paths.raw_records_json)

    df = build_clean_dataframe(records, run_date)
    if df.empty:
        raise ValueError("Cleaning produced no papers; check the raw dataset before indexing.")
    write_csv(df, paths.clean_csv)
    write_json(paths.clean_json, json.loads(df.to_json(orient="records", date_format="iso")))

    print(f"[baseline] Indexing {len(df)} papers")
    index = LocalEmbeddingIndex.build(df, settings, paths.embeddings_json)

    if settings.refresh_test_set or not paths.eval_testset.exists():
        test_set = build_test_set(df, paths.eval_testset)
        write_json(paths.eval_testset, test_set)
    else:
        test_set = read_json(paths.eval_testset)
    if not isinstance(test_set, list) or not test_set:
        raise ValueError("Evaluation set must be a non-empty list.")
    paper_ids = set(df["paper_id"])
    for item in test_set:
        references = item.get("ground_truth_doc_ids")
        if not isinstance(references, list) or not references or not set(references) <= paper_ids:
            raise ValueError("Evaluation references missing papers; rerun with REFRESH_TEST_SET=1.")

    print(f"[baseline] Evaluating {len(test_set)} questions")
    bundle = evaluate_pipeline(
        settings, index, paths.eval_testset, paths.baseline_metrics, paths.baseline_answers,
    )
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, paths.freshness_report)

    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "raw_records": len(records),
        "clean_records": len(df),
        "run_date": run_date.isoformat(),
        "llm_provider": settings.llm_provider,
        "model_name": settings.model_name,
        "embedding_model": settings.embedding_model,
        "top_k": settings.top_k,
        "freshness_threshold_days": settings.freshness_threshold_days,
    }
    generate_phase1_report(paths.baseline_report, source_summary, bundle.summary, quality, freshness)
    print(f"[baseline] Quality={quality.get('success')}, fresh={freshness.get('is_fresh')}")
    print(f"[baseline] Report: {paths.baseline_report}")
    return bundle.summary


def main() -> None:
    run_phase1_pipeline(load_settings())
