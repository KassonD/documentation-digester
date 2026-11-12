import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from langchain_openai import ChatOpenAI

from conftest import failing_llm
from documentation_digester.api.main import app
from documentation_digester.api.routers.chat import get_llm_model
from documentation_digester.settings import settings


@pytest.fixture
def client(fake):
    """Fake LLM, search and memory. Not used as a context manager, so no API key is needed."""
    app.dependency_overrides[get_llm_model] = lambda: fake.llm
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _events(response):
    return [json.loads(line) for line in response.text.splitlines() if line.strip()]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- POST /chat ----------

def test_chat_returns_answer_sources_and_new_session(client):
    response = client.post("/chat", json={"question": "How do signals work?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Use connect()."
    assert body["source"][0] == {"title": "Using signals", "source_path": "getting_started/signals.html"}
    UUID(body["session_id"])


def test_each_new_conversation_gets_its_own_session(client):
    first = client.post("/chat", json={"question": "q"}).json()["session_id"]
    second = client.post("/chat", json={"question": "q"}).json()["session_id"]
    assert first != second


@pytest.mark.parametrize("given, kept", [("abc", "abc"), ("  abc  ", "abc")])
def test_given_session_id_is_reused(client, given, kept):
    assert client.post("/chat", json={"question": "q", "session_id": given}).json()["session_id"] == kept


def test_follow_up_uses_the_conversation_history(client, fake):
    client.post("/chat", json={"question": "How do signals work?", "session_id": "s"})
    client.post("/chat", json={"question": "And in code?", "session_id": "s"})
    assert fake.embedded[-1] == fake.rewrite


@pytest.mark.parametrize(
    "body",
    [{}, {"question": 123}, {"question": None}, {"wrong": "field"},
     {"question": "q", "session_id": ""}, {"question": "q", "session_id": "x" * 129}],
)
def test_bad_request_body_returns_422(client, body):
    assert client.post("/chat", json=body).status_code == 422


def test_only_post_is_allowed(client):
    assert client.get("/chat").status_code == 405


# ---------- POST /chat/stream ----------

def test_stream_returns_ndjson_events(client):
    response = client.post("/chat/stream", json={"question": "How do signals work?", "session_id": "s"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = _events(response)
    assert events[0]["type"] == "sources" and events[0]["session_id"] == "s"
    assert events[-1] == {"type": "done"}


def test_stream_reports_llm_failure_inside_the_stream(client):
    app.dependency_overrides[get_llm_model] = lambda: failing_llm()
    response = client.post("/chat/stream", json={"question": "q"})
    assert response.status_code == 200
    assert _events(response)[-1]["type"] == "error"


# ---------- startup ----------

def test_startup_refuses_to_run_without_an_api_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        with TestClient(app):
            pass


def test_startup_creates_the_configured_model(monkeypatch):
    """Uses a fake key. Creating the client makes no network call."""
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key-not-real")
    with TestClient(app) as started:
        llm = started.app.state.llm
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == settings.OPENROUTER_MODEL
        assert llm.openai_api_base == settings.OPENROUTER_BASE_URL
        assert llm.temperature == 0
    assert app.state.llm is None


# ---------- known bugs ----------

@pytest.mark.xfail(strict=True, reason="BUG-5: an empty question crashes with 500 instead of returning 422")
@pytest.mark.parametrize("question", ["", "   "])
def test_empty_question_returns_422(client, question):
    assert client.post("/chat", json={"question": question}).status_code == 422


@pytest.mark.xfail(strict=True, reason="BUG-6: when the LLM provider is down, /chat returns a bare 500 instead of 503")
def test_llm_outage_returns_503(client):
    app.dependency_overrides[get_llm_model] = lambda: failing_llm()
    assert client.post("/chat", json={"question": "q"}).status_code == 503