"""Public retrieval API without importing the optional tool-agent stack eagerly."""
from importlib import import_module

_EXPORTS = {
    "build_agent": "agent", "run_agent_question": "agent",
    "MiniLMEmbeddings": "embeddings", "LocalEmbeddingIndex": "index", "SearchResult": "index",
    "build_llm": "llm", "AnswerResult": "qa", "answer_question": "qa",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(f".{_EXPORTS[name]}", __name__), name)
    globals()[name] = value
    return value
