from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.reporting import generate_corruption_report
from pipelines.common import experiment_config, fingerprint, observe, require_healthy, save_frame
from retrieval.index import LocalEmbeddingIndex
from pipelines.preflight import require_implementations


def run_corruption_flow_pipeline(settings: Settings) -> dict:
    require_implementations("corruption")
    require_llm_credentials(settings)
    paths = settings.paths
    manifest_path = paths.baseline_metrics.parent / "baseline_run.json"
    if not manifest_path.exists():
        raise FileNotFoundError("Run script/run_phase1.py successfully before the corruption flow.")
    manifest = read_json(manifest_path)
    if manifest["config"] != experiment_config(settings):
        raise ValueError("Provider/model or evaluation settings changed; rerun baseline first.")
    for name, expected in manifest["hashes"].items():
        path = getattr(paths, name)
        if not path.exists() or fingerprint(path) != expected:
            raise ValueError(f"Baseline artifact changed: {name}. Rerun baseline first.")
    baseline = read_json(paths.baseline_metrics)
    clean = pd.DataFrame(read_json(paths.clean_json))
    # Remove the old final report so a failed rerun cannot appear successful.
    paths.comparison_report.unlink(missing_ok=True)
    corrupted = corrupt_clean_dataframe(clean.copy(deep=True), paths.corruption_log)
    save_frame(corrupted, paths.corrupted_clean_csv, paths.corrupted_clean_json)
    corrupted_quality, corrupted_freshness = observe(corrupted, settings, "corrupted")
    # Deliberate experiment: index unhealthy data to quantify its impact.
    print("[corrupted] Experimental gate bypass: measuring the impact of dirty data")
    corrupted_index = LocalEmbeddingIndex.build(corrupted, settings, paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(settings, corrupted_index, paths.eval_testset,
                                         paths.corrupted_metrics, paths.corrupted_answers)

    print("[repaired] Rebuilding from preserved raw records")
    repaired = build_clean_dataframe(load_raw_records(paths.raw_records_json),
                                     datetime.fromisoformat(manifest["run_date"]))
    save_frame(repaired, paths.repaired_clean_csv, paths.repaired_clean_json)
    repaired_quality, repaired_freshness = observe(repaired, settings, "repaired")
    require_healthy(repaired_quality, repaired_freshness, "Repaired")
    repaired_index = LocalEmbeddingIndex.build(repaired, settings, paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(settings, repaired_index, paths.eval_testset,
                                        paths.repaired_metrics, paths.repaired_answers)
    generate_corruption_report(paths.comparison_report, baseline, corrupted_bundle.summary,
                               repaired_bundle.summary, corrupted_quality, repaired_quality,
                               corrupted_freshness, repaired_freshness)
    print(f"{'Metric':24} {'Baseline':>12} {'Corrupted':>12} {'Repaired':>12}")
    for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        print(f"{key:24} {baseline[key]:12.4f} {corrupted_bundle.summary[key]:12.4f} "
              f"{repaired_bundle.summary[key]:12.4f}")
    print(f"[comparison] Complete: {paths.comparison_report}")
    return {"baseline": baseline, "corrupted": corrupted_bundle.summary,
            "repaired": repaired_bundle.summary}


def main() -> None:
    run_corruption_flow_pipeline(load_settings())
