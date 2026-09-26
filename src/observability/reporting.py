from __future__ import annotations

from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the baseline source, evaluation, quality and freshness summary."""
    lines = ["# Phase 1: Baseline Pipeline", "", "## Source and indexing", ""]
    for name, value in source_summary.items():
        lines.append(f"- {name}: {value}")
    lines.extend([
        "", "## Baseline RAG evaluation", "",
        "| Metric | Value |", "| --- | ---: |",
        f"| Samples | {metrics['samples']} |",
        f"| Retrieval Hit Rate | {metrics['retrieval_hit_rate']:.2%} |",
        f"| Mean Token F1 | {metrics['mean_token_f1']:.4f} |",
        f"| Judge accuracy | {metrics['judge_accuracy']:.2%} |",
        f"| Mean judge score | {metrics['mean_judge_score']:.4f} |",
        "", f"Ragas: {metrics.get('ragas', {})}",
        "", "## Great Expectations Quality Gate", "",
        f"- Overall gate: {'PASS' if quality['success'] else 'FAIL'}",
        f"- Great Expectations: {'PASS' if quality['gx_success'] else 'FAIL'}",
        f"- Evaluated expectations: {quality['statistics']['evaluated_expectations']}",
        f"- Successful expectations: {quality['statistics']['successful_expectations']}",
        f"- Failed expectations: {quality['statistics']['unsuccessful_expectations']}",
    ])
    failures = [
        result for result in quality.get('validation_results', {}).get('results', [])
        if not result['success']
    ]
    for result in failures:
        config = result.get('expectation_config', {})
        lines.append(f"- Failed check: {config.get('type', 'unknown')} {config.get('kwargs', {})}")
    lines.extend([
        "", "## Freshness SLA", "",
        f"- Status: {'PASS' if freshness['is_fresh'] else 'FAIL'}",
        f"- Age threshold: {freshness['threshold_days']} days",
        f"- Stale papers: {freshness['stale_rows']} / {freshness['total_rows']}",
        f"- Stale ratio: {freshness['stale_ratio']:.2%}",
        f"- Maximum stale ratio: {freshness['max_stale_ratio']:.2%}",
        f"- Latest publication: {freshness['latest_published']}",
        f"- Oldest publication: {freshness['oldest_published']}",
        "",
    ])
    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")
