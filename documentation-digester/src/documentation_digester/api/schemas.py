
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str

    # Optional for a new conversation.
    # The client should reuse it for follow-up questions.
    session_id: str | None = Field(default=None, max_length=128, min_length=1)
    


class Source(BaseModel):
    title: str
    source_path: str


class ChatResponse(BaseModel):
    answer: str
    source: list[Source]
    session_id: str