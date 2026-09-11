from pydantic import BaseModel

class LoadPaperRequest(BaseModel):
    url: str

class LoadPaperResponse(BaseModel):
    title: str
    summary: str
    suggested_questions: list[str]

class MessageHistory(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[MessageHistory] = []

class Citation(BaseModel):
    quote: str
    section: str

class SourceResponse(BaseModel):
    citations: list[Citation]

class ChatResponse(BaseModel):
    answer: str
    source: SourceResponse | None
    confidence: str

class SessionResponse(BaseModel):
    arxiv_id: str | None
    title: str | None
    summary: str | None
    suggested_questions: list[str]

class AnswerResponse(BaseModel):
    answer: str
    source: SourceResponse | None
    confidence: str