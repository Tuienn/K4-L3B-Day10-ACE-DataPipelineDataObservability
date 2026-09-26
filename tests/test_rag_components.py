"""Focused tests of caching and index failure safety without downloading models."""
import importlib.util
from pathlib import Path
import sys
import types
from unittest.mock import Mock

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def load_module(monkeypatch, name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def test_embedding_cache_returns_independent_vectors(monkeypatch):
    backend = Mock()
    backend.encode.return_value.tolist.return_value = [[0.1, 0.2]]
    transformer = types.ModuleType("sentence_transformers")
    transformer.SentenceTransformer = Mock(return_value=backend)
    embeddings = types.ModuleType("langchain_core.embeddings")
    embeddings.Embeddings = object
    monkeypatch.setitem(sys.modules, "sentence_transformers", transformer)
    monkeypatch.setitem(sys.modules, "langchain_core.embeddings", embeddings)
    module = load_module(monkeypatch, "_test_embeddings", "retrieval/embeddings.py")
    first = module.MiniLMEmbeddings("test")
    second = module.MiniLMEmbeddings("test")
    vectors = first.embed_documents(["same text"])
    vectors[0][0] = 999
    assert second.embed_documents(["same text"]) == [[0.1, 0.2]]
    assert second.embed_query("same text") == [0.1, 0.2]
    assert first.embed_documents([]) == []
    backend.encode.assert_called_once()
    transformer.SentenceTransformer.assert_called_once()


def test_gemini_client_reused_and_credentials_not_logged(monkeypatch, tmp_path):
    from dataclasses import replace
    from core.config import load_settings
    provider = types.ModuleType("langchain_google_genai")
    provider.ChatGoogleGenerativeAI = Mock()
    monkeypatch.setitem(sys.modules, "langchain_google_genai", provider)
    module = load_module(monkeypatch, "_test_llm", "retrieval/llm.py")
    settings = replace(load_settings(tmp_path), llm_provider="gemini", google_api_key="test-only")
    assert module.build_llm(settings) is module.build_llm(settings)
    provider.ChatGoogleGenerativeAI.assert_called_once()
    assert provider.ChatGoogleGenerativeAI.call_args.kwargs["timeout"] == 60


@pytest.fixture
def index_module(monkeypatch):
    chroma = types.ModuleType("chromadb")
    chroma.PersistentClient = Mock()
    errors = types.ModuleType("chromadb.errors")
    errors.NotFoundError = type("NotFoundError", (Exception,), {})
    embeddings = types.ModuleType("retrieval.embeddings")
    embeddings.MiniLMEmbeddings = Mock()
    monkeypatch.setitem(sys.modules, "chromadb", chroma)
    monkeypatch.setitem(sys.modules, "chromadb.errors", errors)
    monkeypatch.setitem(sys.modules, "retrieval.embeddings", embeddings)
    module = load_module(monkeypatch, "_test_index", "retrieval/index.py")
    return module, chroma, embeddings


def test_embedding_failure_preserves_old_collection(index_module, tmp_path):
    from core.config import load_settings
    module, chroma, embeddings = index_module
    settings = load_settings(tmp_path)
    row = {key: "value" for key in ("paper_id", "title", "text_for_embedding", "published",
            "authors_joined", "categories_joined", "summary", "abs_url", "pdf_url")}
    embeddings.MiniLMEmbeddings.return_value.embed_documents.side_effect = RuntimeError("model unavailable")
    with pytest.raises(RuntimeError, match="model unavailable"):
        module.LocalEmbeddingIndex.build(pd.DataFrame([row]), settings)
    chroma.PersistentClient.assert_not_called()


def test_search_bounds_and_empty_collection(index_module):
    module, _, _ = index_module
    index = object.__new__(module.LocalEmbeddingIndex)
    index.settings = types.SimpleNamespace(top_k=4)
    index.collection = Mock()
    index.embedding_model = Mock()
    index.collection.count.return_value = 0
    assert index.search("question") == []
    index.embedding_model.embed_query.assert_not_called()
    index.collection.count.return_value = 2
    index.collection.query.return_value = {}
    assert index.search("question", top_k=10) == []
    assert index.collection.query.call_args.kwargs["n_results"] == 2
    with pytest.raises(ValueError, match="top_k"):
        index.search("question", top_k=0)


def test_metric_counts_repetition_and_discloses_judge_fallback(monkeypatch, tmp_path):
    pytest.importorskip("pydantic")
    from dataclasses import replace
    from core.config import load_settings
    for name, attrs in {
        "retrieval.embeddings": ("MiniLMEmbeddings",),
        "retrieval.index": ("LocalEmbeddingIndex",),
        "retrieval.llm": ("build_llm",),
        "retrieval.qa": ("answer_question",),
    }.items():
        module = types.ModuleType(name)
        for attr in attrs:
            setattr(module, attr, Mock())
        monkeypatch.setitem(sys.modules, name, module)
    metrics = load_module(monkeypatch, "_test_metrics", "evaluation/metrics.py")
    assert metrics._token_f1("a a b", "a b b") == pytest.approx(2 / 3)
    settings = replace(load_settings(tmp_path), llm_provider="gemini", google_api_key="test-only")
    metrics.build_llm.return_value.with_structured_output.return_value.invoke.side_effect = RuntimeError("offline")
    verdict = metrics._judge_answer(settings, "question", "answer", "answer")
    assert verdict.backend == "heuristic"
    assert verdict.score == 5
    metrics._judge_answer(settings, "other question", "a", "b")
    metrics.build_llm.assert_called_once()
    path = tmp_path / "empty.json"
    path.write_text("[]")
    with pytest.raises(ValueError, match="empty"):
        metrics.evaluate_pipeline(settings, Mock(), path, tmp_path / "metrics.json", tmp_path / "answers.json")
