from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat",tags=["Chat"])

class QuestionRequest(BaseModel):
    question: str

class Source(BaseModel):
    title: str
    source_path: str

class ChatResponse(BaseModel):
    answer: str
    source: list[Source]

# mock response for now
@router.post("", response_model=ChatResponse)
def ask(body: QuestionRequest):
    return ChatResponse(
        answer=f"this is a fake answer to: {body.question}",
        source=[
            Source(
                title = "A Fake Source",
                source_path ="project/fake_source.html"
            )
        ],
    )


