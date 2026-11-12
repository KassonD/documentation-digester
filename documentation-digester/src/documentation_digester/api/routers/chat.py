
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.language_models import BaseChatModel

from documentation_digester.api.schemas import ChatResponse, QuestionRequest
from documentation_digester.service.retrieval import answer_from_docs, stream_answer_from_docs


router = APIRouter(prefix="/chat", tags=["Chat"])


def get_llm_model(request: Request) -> BaseChatModel:
    return request.app.state.llm

@router.post("", response_model=ChatResponse)
def ask(
    body: QuestionRequest,
    llm: BaseChatModel = Depends(get_llm_model),
):


    session_id = (
        body.session_id.strip()
        if body.session_id and body.session_id.strip()
        else str(uuid4())
    )


    return answer_from_docs(body.question, llm, session_id)


@router.post("/stream")
def ask_stream(
    body: QuestionRequest,
    llm: BaseChatModel = Depends(get_llm_model),
):


    session_id = (
        body.session_id.strip()
        if body.session_id and body.session_id.strip()
        else str(uuid4())
    )


    return StreamingResponse(
        stream_answer_from_docs(body.question, llm, session_id),
        media_type="application/x-ndjson",
    )


