"""Orchestration contract tests: no network, real pandas, stub teammate modules/LLM/index."""
from dataclasses import replace
import importlib
from pathlib import Path
import sys
import types
from unittest.mock import Mock

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def lab(tmp_path, monkeypatch):
    # Avoid importing model SDKs or student implementations in isolated contract tests.
    packages = ("pipelines", "retrieval", "evaluation", "observability", "ingestion")
    for name in packages:
        package = types.ModuleType(name)
        package.__path__ = [str(ROOT / "src" / name)]
        monkeypatch.setitem(sys.modules, name, package)
    members = {
        "retrieval.index": ("LocalEmbeddingIndex", "SearchResult"),
        "retrieval.llm": ("build_llm",),
        "evaluation.metrics": ("evaluate_pipeline",),
        "evaluation.testset": ("build_test_set",),
        "ingestion.cleaning": ("build_clean_dataframe",),
        "ingestion.crossref": ("fetch_source_records", "load_raw_records"),
        "ingestion.corruption": ("corrupt_clean_dataframe",),
        "observability.quality": ("run_data_quality_checks", "build_freshness_report"),
        "observability.reporting": ("generate_phase1_report", "generate_corruption_report"),
    }
    mocks = {}
    for name, names in members.items():
        module = types.ModuleType(name)
        for attr in names:
            value = Mock(name=attr)
            setattr(module, attr, value)
            mocks[attr] = value
        monkeypatch.setitem(sys.modules, name, module)
    for name in ("pipelines.common", "pipelines.phase1", "pipelines.corruption_flow", "retrieval.qa"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    from core.config import load_settings
    from core.utils import write_json, write_text
    settings = replace(load_settings(tmp_path), llm_provider="gemini", google_api_key="test-only",
                       model_name="test-model", refresh_source=False, refresh_test_set=False)
    p = settings.paths
    write_json(p.raw_records_json, [{"paper_id": "doi:1"}])
    row = dict(paper_id="doi:1", title="A paper", published="2026-09-20", summary="A sufficiently long summary for this paper.",
               authors_joined="A Author", categories_joined="AI", abs_url="https://example.org", pdf_url="",
               text_for_embedding="Title: A paper\nSummary: A sufficiently long summary for this paper.", age_days=6)
    frame = pd.DataFrame([row])
    mocks["load_raw_records"].return_value = [{"paper_id": "doi:1"}]
    mocks["build_clean_dataframe"].side_effect = lambda records, date: frame.copy(deep=True)
    mocks["build_test_set"].return_value = [dict(id="q1", question_type="summary", question="Summarize", ground_truth="Summary", ground_truth_doc_ids=["doi:1"])]
    mocks["run_data_quality_checks"].side_effect = lambda df, settings, stage: {"success": stage != "corrupted"}
    mocks["build_freshness_report"].return_value = {"is_fresh": True}
    mocks["corrupt_clean_dataframe"].side_effect = lambda df, log: df.assign(summary="", text_for_embedding="broken")
    metrics = dict(retrieval_hit_rate=1., mean_token_f1=.8, judge_accuracy=1., mean_judge_score=5.)

    def evaluate(settings, index, test_path, metrics_path, answers_path):
        write_json(metrics_path, metrics)
        write_json(answers_path, [])
        return types.SimpleNamespace(summary=metrics, answers=[])
    mocks["evaluate_pipeline"].side_effect = evaluate
    mocks["generate_phase1_report"].side_effect = lambda path, *args: write_text(path, "baseline")
    mocks["generate_corruption_report"].side_effect = lambda path, *args: write_text(path, "comparison")
    phase1 = importlib.import_module("pipelines.phase1")
    flow = importlib.import_module("pipelines.corruption_flow")
    monkeypatch.setattr(phase1, "require_implementations", lambda stage: None)
    monkeypatch.setattr(flow, "require_implementations", lambda stage: None)
    qa = importlib.import_module("retrieval.qa")
    yield types.SimpleNamespace(settings=settings, mocks=mocks, frame=frame, phase1=phase1, flow=flow, qa=qa)
    for name in ("pipelines.common", "pipelines.phase1", "pipelines.corruption_flow", "retrieval.qa"):
        sys.modules.pop(name, None)


def test_three_stages_share_testset_and_repair_date(lab):
    lab.phase1.run_phase1_pipeline(lab.settings)
    before = lab.settings.paths.raw_records_json.read_bytes()
    lab.flow.run_corruption_flow_pipeline(lab.settings)
    lab.flow.run_corruption_flow_pipeline(lab.settings)
    assert lab.mocks["build_test_set"].call_count == 1
    assert all(call.args[2] == lab.settings.paths.eval_testset for call in lab.mocks["evaluate_pipeline"].call_args_list)
    dates = [call.args[1] for call in lab.mocks["build_clean_dataframe"].call_args_list]
    assert dates[0] == dates[1] == dates[2]
    assert lab.settings.paths.raw_records_json.read_bytes() == before
    lab.mocks["fetch_source_records"].assert_not_called()
    paths = [call.args[2] for call in lab.mocks["LocalEmbeddingIndex"].build.call_args_list]
    assert paths[:3] == [lab.settings.paths.embeddings_json, lab.settings.paths.corrupted_embeddings_json,
                         lab.settings.paths.repaired_embeddings_json]
    assert lab.settings.paths.comparison_report.exists()


def test_baseline_gate_stops_before_index(lab):
    lab.mocks["run_data_quality_checks"].side_effect = None
    lab.mocks["run_data_quality_checks"].return_value = {"success": False}
    with pytest.raises(ValueError, match="gate failed"):
        lab.phase1.run_phase1_pipeline(lab.settings)
    lab.mocks["LocalEmbeddingIndex"].build.assert_not_called()
    assert not (lab.settings.paths.baseline_metrics.parent / "baseline_run.json").exists()


def test_freshness_gate_stops_before_index(lab):
    lab.mocks["build_freshness_report"].return_value = {"is_fresh": False}
    with pytest.raises(ValueError, match="gate failed"):
        lab.phase1.run_phase1_pipeline(lab.settings)
    lab.mocks["LocalEmbeddingIndex"].build.assert_not_called()


def test_missing_baseline_is_actionable(lab):
    with pytest.raises(FileNotFoundError, match="run_phase1.py"):
        lab.flow.run_corruption_flow_pipeline(lab.settings)


@pytest.mark.parametrize("artifact", ["eval_testset", "raw_records_json", "clean_json", "baseline_metrics"])
def test_changed_artifact_rejected(lab, artifact):
    lab.phase1.run_phase1_pipeline(lab.settings)
    getattr(lab.settings.paths, artifact).write_text("[]")
    with pytest.raises(ValueError, match="artifact changed"):
        lab.flow.run_corruption_flow_pipeline(lab.settings)
    lab.mocks["corrupt_clean_dataframe"].assert_not_called()


def test_changed_model_rejected(lab):
    lab.phase1.run_phase1_pipeline(lab.settings)
    with pytest.raises(ValueError, match="settings changed"):
        lab.flow.run_corruption_flow_pipeline(replace(lab.settings, model_name="different"))


def test_stale_testset_rejected(lab):
    lab.mocks["build_test_set"].return_value[0]["ground_truth_doc_ids"] = ["missing"]
    with pytest.raises(ValueError, match="absent papers"):
        lab.phase1.run_phase1_pipeline(lab.settings)
    lab.mocks["LocalEmbeddingIndex"].build.assert_not_called()


def test_gemini_answers_from_context(lab):
    index = Mock()
    index.search.return_value = [types.SimpleNamespace(paper_id="doi:1", title="A paper", content="Context-only fact")]
    llm = lab.mocks["build_llm"].return_value
    llm.invoke.return_value.content = [{"type": "text", "text": "Gemini answer"}]
    result = lab.qa.answer_question("Summarize", lab.settings, index)
    assert result.answer == "Gemini answer"
    assert result.retrieved_doc_ids == ["doi:1"]
    assert "Context-only fact" in llm.invoke.call_args.args[0][1][1]
    llm.invoke.side_effect = RuntimeError("provider unavailable")
    with pytest.raises(RuntimeError, match="provider unavailable"):
        lab.qa.answer_question("Summarize", lab.settings, index)


def test_no_context_does_not_call_gemini(lab):
    index = Mock()
    index.search.return_value = []
    result = lab.qa.answer_question("Summarize", lab.settings, index)
    assert "don't know" in result.answer
    lab.mocks["build_llm"].assert_not_called()


def test_preflight_detects_only_unconditional_placeholders(tmp_path):
    from pipelines.preflight import STAGES, implementation_issues
    for path, names in STAGES["baseline"].items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(f"def {name}():\n    return None\n" for name in names))
    target = tmp_path / "observability/reporting.py"
    target.write_text("def generate_phase1_report():\n    raise NotImplementedError('TODO')\n")
    assert implementation_issues("baseline", tmp_path) == [
        "observability/reporting.py: generate_phase1_report() is not implemented"]
    target.write_text("def generate_phase1_report():\n    if False:\n        raise NotImplementedError('optional branch')\n")
    assert implementation_issues("baseline", tmp_path) == []


def test_invalid_top_k_rejected_before_query(lab):
    index = Mock()
    with pytest.raises(ValueError, match="top_k"):
        lab.qa.answer_question("Summarize", lab.settings, index, top_k=0)
    index.search.assert_not_called()


def test_quoted_title_with_apostrophe(lab):
    index = Mock()
    index.lookup.return_value = None
    index.search.return_value = []
    lab.qa.answer_question("Who authored the paper 'An agent's memory'?", lab.settings, index)
    index.lookup.assert_called_once_with("An agent's memory")


def test_repaired_gate_stops_before_repaired_index(lab):
    lab.phase1.run_phase1_pipeline(lab.settings)
    lab.mocks["run_data_quality_checks"].side_effect = lambda df, settings, stage: {"success": False}
    with pytest.raises(ValueError, match="Repaired"):
        lab.flow.run_corruption_flow_pipeline(lab.settings)
    assert lab.mocks["LocalEmbeddingIndex"].build.call_count == 2
    lab.mocks["generate_corruption_report"].assert_not_called()


def test_new_baseline_config_invalidates_old_metrics(lab):
    import json
    lab.phase1.run_phase1_pipeline(lab.settings)
    path = lab.settings.paths.baseline_metrics.parent / "baseline_run.json"
    manifest = json.loads(path.read_text())
    manifest["config"].pop("evaluation_version")
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="settings changed"):
        lab.flow.run_corruption_flow_pipeline(lab.settings)
