from __future__ import annotations

import argparse

from core.config import load_settings, require_llm_credentials
from pipelines.preflight import implementation_issues


def main(stage: str) -> None:
    parser = argparse.ArgumentParser(description=f"Run the {stage} RAG pipeline")
    parser.add_argument("--check", action="store_true", help="Check module readiness and credentials without API calls")
    args = parser.parse_args()
    issues = implementation_issues(stage)
    settings = load_settings()
    try:
        require_llm_credentials(settings)
    except RuntimeError as exc:
        issues.append(str(exc))
    if stage == "corruption" and not (settings.paths.baseline_metrics.parent / "baseline_run.json").exists():
        issues.append("Complete run_phase1.py first: baseline_run.json is missing")
    if issues:
        for issue in issues:
            print(f"[BLOCKED] {issue}")
        raise SystemExit(1)
    if args.check:
        print(f"[OK] {stage}: module placeholders and credentials checked; no API/model calls made.")
        print("Run without --check to verify runtime dependencies, data quality and provider access.")
        return
    if stage == "baseline":
        from pipelines.phase1 import run_phase1_pipeline
        run_phase1_pipeline(settings)
    else:
        from pipelines.corruption_flow import run_corruption_flow_pipeline
        run_corruption_flow_pipeline(settings)
