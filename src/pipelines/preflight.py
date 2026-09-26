"""Check teammate contracts before spending time/API calls on a pipeline."""
from __future__ import annotations

import ast
from pathlib import Path


COMMON = {
    "ingestion/crossref.py": ("load_raw_records",),
    "ingestion/cleaning.py": ("build_clean_dataframe",),
    "observability/quality.py": ("run_data_quality_checks", "build_freshness_report"),
}
STAGES = {
    "baseline": {
        **COMMON,
        "ingestion/crossref.py": ("load_raw_records", "fetch_source_records", "parse_crossref_payload"),
        "evaluation/testset.py": ("build_test_set",),
        "observability/reporting.py": ("generate_phase1_report",),
    },
    "corruption": {
        **COMMON,
        "ingestion/corruption.py": ("corrupt_clean_dataframe",),
        "observability/reporting.py": ("generate_corruption_report",),
    },
}


def implementation_issues(stage: str, source_dir: Path | None = None) -> list[str]:
    root = source_dir or Path(__file__).resolve().parents[1]
    issues = []
    for relative, names in STAGES[stage].items():
        try:
            tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            issues.append(f"{relative}: {type(exc).__name__}")
            continue
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        for name in names:
            function = functions.get(name)
            if function is None:
                issues.append(f"{relative}: missing {name}()")
                continue
            # Detect the scaffold's unconditional placeholder, not legitimate error branches.
            if any(isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                   and isinstance(node.exc.func, ast.Name) and node.exc.func.id == "NotImplementedError"
                   for node in function.body):
                issues.append(f"{relative}: {name}() is not implemented")
    return issues


def require_implementations(stage: str) -> None:
    issues = implementation_issues(stage)
    if issues:
        raise RuntimeError("Cannot run pipeline yet:\n- " + "\n- ".join(issues))
