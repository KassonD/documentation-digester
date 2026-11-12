import json

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from conftest import MATCHES, failing_llm
from documentation_digester.api.schemas import Source
from documentation_digester.service import retrieval


def ask(fake, question="How do signals work?", session="s1", llm=None):
    return retrieval.answer_from_docs(question, llm or fake.llm, session)


def stream(fake, question="How do signals work?", session="s1", llm=None):
    lines = retrieval.stream_answer_from_docs(question, llm or fake.llm, session)
    return [json.loads(line) for line in lines]


# ---------- answer_from_docs ----------

def test_returns_answer_sources_and_session(fake):
    response = ask(fake)
    assert response.answer == "Use connect()."
    assert [s.source_path for s in response.source] == ["getting_started/signals.html"] * 2
    assert response.source[0].title == "Using signals"
    assert response.session_id == "s1"


def test_first_question_is_searched_as_asked_with_top_4(fake):
    ask(fake, "  How do signals work?  ")
    assert fake.embedded == ["How do signals work?"]
    assert fake.search_calls == [([0.1, 0.2, 0.3], 4)]
    assert len(fake.prompts) == 1


def test_prompt_contains_question_and_every_retrieved_chunk(fake):
    ask(fake)
    assert "How do signals work?" in fake.prompts[0]
    assert all(m["text"] in fake.prompts[0] for m in MATCHES)


def test_conversation_is_saved(fake):
    ask(fake, "  How do signals work?  ")
    messages = fake.history("s1").messages
    assert [m.content for m in messages] == ["How do signals work?", "Use connect()."]


def test_follow_up_is_rewritten_for_search_but_answered_as_asked(fake):
    ask(fake, "How do signals work?")
    ask(fake, "And in code?")
    assert fake.embedded[-1] == fake.rewrite
    answer_prompt = fake.prompts[-1]
    assert "And in code?" in answer_prompt
    assert "How do signals work?" in answer_prompt


def test_blank_rewrite_falls_back_to_the_original_question(fake):
    ask(fake, "How do signals work?")
    fake.rewrite = "   "
    ask(fake, "And in code?")
    assert fake.embedded[-1] == "And in code?"


def test_sessions_do_not_share_history(fake):
    ask(fake, "How do signals work?", session="a")
    ask(fake, "What is a scene?", session="b")
    assert fake.embedded == ["How do signals work?", "What is a scene?"]
    assert len(fake.history("b").messages) == 2


def test_no_matches_skips_the_llm_but_still_saves(fake):
    fake.matches = []
    response = ask(fake)
    assert response.source == []
    assert "not have enough information" in response.answer
    assert fake.prompts == []
    assert len(fake.history("s1").messages) == 2


@pytest.mark.parametrize("metadata", [{}, None])
def test_missing_metadata_falls_back_to_unknown(fake, metadata):
    fake.matches = [{"id": "x", "text": "t", "distance": 0.0, "metadata": metadata}]
    assert ask(fake).source[0] == Source(title="Unknown", source_path="Unknown")


@pytest.mark.parametrize("question", ["", "   ", None])
def test_blank_question_is_rejected_before_anything_runs(fake, question):
    with pytest.raises(ValueError):
        ask(fake, question)
    assert fake.embedded == [] and fake.histories == {}


# ---------- stream_answer_from_docs ----------

def test_stream_sends_sources_then_tokens_then_done(fake):
    events = stream(fake)
    assert events[0] == {
        "type": "sources",
        "session_id": "s1",
        "sources": [{"title": "Using signals", "source_path": "getting_started/signals.html"}] * 2,
    }
    assert events[-1] == {"type": "done"}
    assert "".join(e["text"] for e in events if e["type"] == "token") == "Use connect()."


def test_stream_sends_the_answer_piece_by_piece(fake):
    text = "Call connect() on the signal from your script."
    llm = GenericFakeChatModel(messages=iter([AIMessage(content=text)]))
    tokens = [e["text"] for e in stream(fake, llm=llm) if e["type"] == "token"]
    assert len(tokens) > 1
    assert "".join(tokens) == text


def test_stream_saves_the_full_answer(fake):
    stream(fake)
    assert [m.content for m in fake.history("s1").messages] == ["How do signals work?", "Use connect()."]


def test_stream_with_no_matches_skips_the_llm(fake):
    fake.matches = []
    events = stream(fake)
    assert events[0]["sources"] == []
    assert "not have enough information" in events[1]["text"]
    assert events[-1] == {"type": "done"}
    assert fake.prompts == []


def test_stream_replaces_an_empty_answer(fake):
    fake.answer = ""
    tokens = [e["text"] for e in stream(fake) if e["type"] == "token"]
    assert tokens == ["I don't know."]


def test_stream_reports_llm_failure_as_an_error_event(fake):
    events = stream(fake, llm=failing_llm())
    assert events[-1] == {"type": "error", "message": "LLM provider unreachable"}
    assert {"type": "done"} not in events


def test_stream_reports_blank_question_as_an_error_event(fake):
    events = stream(fake, question="  ")
    assert events == [{"type": "error", "message": "Question cannot be empty."}]
    assert fake.embedded == []


# ---------- known gaps ----------

@pytest.mark.xfail(strict=True, reason="GAP-1: sources give the page title but not the section, so a citation can't point to the exact section")
def test_sources_name_the_section():
    assert "section" in Source.model_fields