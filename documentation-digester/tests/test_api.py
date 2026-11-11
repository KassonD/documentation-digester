import pytest
from fastapi.testclient import TestClient
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama

from documentation_digester.api.main import app
from documentation_digester.api.routers.chat import get_llm_model
from documentation_digester.service import retrieval
from documentation_digester.settings import settings

MATCH = {"id": "1", "text": "Use connect().", "distance": 0.1,
         "metadata": {"title": "Using signals", "source_path": "getting_started/signals.html"}}


def _llm(reply="Use connect()."):
    def run(_prompt):
        if isinstance(reply, Exception):
            raise reply
        return reply

    return RunnableLambda(run)


@pytest.fixture
def client(monkeypatch):
    """Client with a fake LLM and fake search. Not used as a context manager, so Ollama is never started."""
    monkeypatch.setattr(retrieval, "embed_query", lambda q: [0.1, 0.2] if q.strip() else retrieval_error())
    monkeypatch.setattr(retrieval, "search_chunks", lambda vector, top_k=5: [MATCH])
    app.dependency_overrides[get_llm_model] = lambda: _llm()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def retrieval_error():
    raise ValueError("Question cannot be empty.")


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_answer_and_sources(client):
    response = client.post("/chat", json={"question": "How do signals work?"})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "Use connect().",
        "source": [{"title": "Using signals", "source_path": "getting_started/signals.html"}],
    }


@pytest.mark.parametrize("body", [{}, {"question": 123}, {"question": None}, {"wrong": "field"}])
def test_bad_request_body_returns_422(client, body):
    assert client.post("/chat", json=body).status_code == 422


def test_only_post_is_allowed(client):
    assert client.get("/chat").status_code == 405


def test_startup_creates_the_configured_ollama_model():
    with TestClient(app) as started:
        llm = started.app.state.llm
        assert isinstance(llm, ChatOllama)
        assert llm.model == settings.OLLAMA_MODEL
        assert llm.temperature == 0
    assert app.state.llm is None


@pytest.mark.xfail(strict=True, reason="BUG-5: an empty question crashes with 500 instead of returning 422")
@pytest.mark.parametrize("question", ["", "   "])
def test_empty_question_returns_422(client, question):
    assert client.post("/chat", json={"question": question}).status_code == 422


@pytest.mark.xfail(strict=True, reason="BUG-6: when Ollama is down the API returns a bare 500 instead of 503")
def test_llm_outage_returns_503(client):
    app.dependency_overrides[get_llm_model] = lambda: _llm(ConnectionError("Ollama not running"))
    assert client.post("/chat", json={"question": "q"}).status_code == 503