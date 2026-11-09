from chromadb import Embeddings
from documentation_digester.service.retrieval import answer_from_docs
from fastapi import APIRouter, Depends, Request
from documentation_digester.api.schemas import ChatResponse,QuestionRequest
from langchain_core.language_models import BaseChatModel
from documentation_digester.digester.embeddings import embed_documents,embed_query

router = APIRouter(prefix="/chat",tags=["Chat"])


def get_llm_model(request: Request) -> BaseChatModel:
    return request.app.state.llm

# mock response for now
@router.post("", response_model=ChatResponse)
def ask(
    body: QuestionRequest,
    llm: BaseChatModel = Depends(get_llm_model),
    ):
    return answer_from_docs(body.question,llm)
    


