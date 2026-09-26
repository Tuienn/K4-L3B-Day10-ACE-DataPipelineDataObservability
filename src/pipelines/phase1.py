from __future__ import annotations

import logging
from typing import Any

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


def run_phase1_pipeline(settings: Settings) -> dict[str, Any]:
    """Run the clean baseline and save its evaluation and quality reports."""
    paths = settings.paths
    run_date = now_utc()

    logger.info("[1/6] Ingest source records")
    if settings.refresh_source or not paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(paths.raw_records_json)

    logger.info("[2/6] Clean %d source records", len(records))
    df = build_clean_dataframe(records, run_date)
    write_csv(df, paths.clean_csv)
    write_json(paths.clean_json, df.to_dict(orient="records"))
    if df.empty:
        raise ValueError("No valid papers remain after cleaning; cannot build the baseline index.")

    logger.info("[3/6] Build ChromaDB index for %d papers", len(df))
    index = LocalEmbeddingIndex.build(df, settings, paths.embeddings_json)

    logger.info("[4/6] Build or load evaluation test set")
    if settings.refresh_test_set or not paths.eval_testset.exists():
        test_set = build_test_set(df, paths.eval_testset)
    else:
        test_set = read_json(paths.eval_testset)
    if not test_set:
        raise ValueError("The evaluation test set is empty; refresh it before running the baseline.")

    logger.info("[5/6] Evaluate baseline RAG on %d questions", len(test_set))
    evaluation = evaluate_pipeline(
        settings, index, paths.eval_testset, paths.baseline_metrics, paths.baseline_answers
    )

    logger.info("[6/6] Run Great Expectations quality gate and freshness checks")
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings)
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "run_date": run_date.isoformat(),
        "raw_records": len(records),
        "clean_records": len(df),
        "indexed_documents": len(index.documents),
        "test_questions": len(test_set),
        "collection_name": index.collection_name,
        "embedding_model": settings.embedding_model,
    }
    generate_phase1_report(
        paths.baseline_report, source_summary, evaluation.summary, quality, freshness
    )
    logger.info("Baseline report saved to %s", paths.baseline_report)
    if not quality["success"]:
        raise RuntimeError(
            f"Baseline quality gate failed. See {paths.baseline_quality_report} "
            f"and {paths.baseline_report}."
        )
    return {
        "source_summary": source_summary,
        "metrics": evaluation.summary,
        "quality": quality,
        "freshness": freshness,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    result = run_phase1_pipeline(load_settings())
    metrics = result["metrics"]
    print(
        "Phase 1 completed: "
        f"{result['source_summary']['clean_records']} papers, "
        f"Hit Rate = {metrics['retrieval_hit_rate']:.2%}, "
        f"Token F1 = {metrics['mean_token_f1']:.4f}, Quality Gate = PASS"
    )


if __name__ == "__main__":
    main()
