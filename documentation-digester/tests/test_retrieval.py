import pytest
from langchain_core.runnables import RunnableLambda

from documentation_digester.api.schemas import Source
from documentation_digester.service import retrieval

MATCHES = [
    {"id": "1", "text": "Use connect() to link a signal.", "distance": 0.1,
     "metadata": {"title": "Using signals", "source_path": "getting_started/signals.html"}},
    {"id": "2", "text": "Custom signals are declared with the signal keyword.", "distance": 0.2,
     "metadata": {"title": "Using signals", "source_path": "getting_started/signals.html"}},
]


class Recorder:
    """Stands in for embed_query, search_chunks and the LLM, and records how each was called."""

    def __init__(self, matches=MATCHES, answer="Use connect()."):
        self.matches, self.answer = matches, answer
        self.search_calls, self.prompts = [], []

    def embed(self, question):
        return [0.1, 0.2, 0.3]

    def search(self, vector, top_k=5):
        self.search_calls.append((vector, top_k))
        return self.matches

    @property
    def llm(self):
        def reply(prompt_value):
            self.prompts.append(prompt_value.to_string())
            return self.answer

        return RunnableLambda(reply)


@pytest.fixture
def rec(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(retrieval, "embed_query", recorder.embed)
    monkeypatch.setattr(retrieval, "search_chunks", recorder.search)
    return recorder


def test_returns_llm_answer_and_sources_in_rank_order(rec):
    response = retrieval.answer_from_docs("How do signals work?", rec.llm)
    assert response.answer == "Use connect()."
    assert [s.source_path for s in response.source] == ["getting_started/signals.html"] * 2
    assert response.source[0].title == "Using signals"


def test_searches_with_the_query_embedding_and_top_4(rec):
    retrieval.answer_from_docs("q", rec.llm)
    assert rec.search_calls == [([0.1, 0.2, 0.3], 4)]


def test_prompt_contains_question_and_every_retrieved_chunk(rec):
    retrieval.answer_from_docs("How do signals work?", rec.llm)
    prompt = rec.prompts[0]
    assert "How do signals work?" in prompt
    assert all(m["text"] in prompt for m in MATCHES)


def test_no_matches_skips_the_llm(rec):
    rec.matches = []
    response = retrieval.answer_from_docs("q", rec.llm)
    assert response.source == []
    assert "not have enough information" in response.answer
    assert rec.prompts == []


def test_missing_metadata_falls_back_to_unknown(rec):
    rec.matches = [{"id": "x", "text": "t", "distance": 0.0, "metadata": {}}]
    response = retrieval.answer_from_docs("q", rec.llm)
    assert response.source[0] == Source(title="Unknown", source_path="Unknown")


def test_blank_question_is_rejected_before_searching(monkeypatch):
    called = []
    monkeypatch.setattr(retrieval, "search_chunks", lambda *a, **k: called.append(1))
    with pytest.raises(ValueError):
        retrieval.answer_from_docs("   ", llm=None)
    assert called == []


@pytest.mark.xfail(strict=True, reason="GAP-1: sources give the page title but not the section, so a citation can't point to the exact section")
def test_sources_name_the_section():
    assert "section" in Source.model_fields