from contextlib import asynccontextmanager

from documentation_digester.api.routers import chat
from documentation_digester.settings import settings
from fastapi import FastAPI
from langchain_openai import ChatOpenAI


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    app.state.llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0,
        default_headers={"X-OpenRouter-Title": "Godot Docbot"},
        # Free models often stream the answer as reasoning and leave content empty.
        extra_body={"reasoning": {"exclude": True}},
    )

    yield

    app.state.llm = None


app = FastAPI(lifespan=lifespan)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
