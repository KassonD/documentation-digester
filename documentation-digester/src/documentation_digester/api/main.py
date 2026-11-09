from contextlib import asynccontextmanager

from fastapi import FastAPI
from documentation_digester.api.routers import chat

app = FastAPI()
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status": "ok"}

