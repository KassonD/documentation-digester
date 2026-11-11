from contextlib import asynccontextmanager

from documentation_digester.settings import settings
from fastapi import FastAPI
from documentation_digester.api.routers import chat
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings



# can also set keep_alive to '-1' to keep it alive indefinitely 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    app.state.llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0,
        keep_alive="30m",
        reasoning=False,
    )
   

    yield

    # Application shutdown
    app.state.llm = None

app = FastAPI(lifespan=lifespan)
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status": "ok"}

