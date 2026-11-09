from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str

class Source(BaseModel):
    title: str
    source_path: str

class ChatResponse(BaseModel):
    answer: str
    source: list[Source]
