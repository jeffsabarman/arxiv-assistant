from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from paper import fetch_paper
from chunker import chunk_sections
from embedder import embed_chunks
from rag import answer, generate_summary, generate_suggested_questions

from schemas_model import (
    LoadPaperResponse,
    LoadPaperRequest,
    ChatResponse,
    ChatRequest,
    SourceResponse,
    SessionResponse,
    Citation
)

HISTORY_MESSAGES = 6

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# In-memory session state
session = {
    "arxiv_id": None,
    "title": None,
    "summary": None,
    "suggested_questions": []
}

@app.get("/")
async def root():
    return {"message": "ArXiv Assistant API"}

@app.post("/paper", response_model=LoadPaperResponse)
async def load_paper(request: LoadPaperRequest):
    try:
      metadata, sections, arxiv_id  = fetch_paper(request.url)
      chunks = chunk_sections(sections)
      embed_chunks(chunks, arxiv_id)

      summary = generate_summary(arxiv_id)
      suggested_questions = generate_suggested_questions(arxiv_id)

      session["arxiv_id"] = arxiv_id
      session["title"] = metadata.title
      session["summary"] = summary
      session["suggested_questions"] = suggested_questions

      return LoadPaperResponse(
         title=metadata.title,
         summary=summary,
         suggested_questions=suggested_questions
      )
    except ValueError as e:
       raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not session["arxiv_id"]:
      raise HTTPException(
         status_code=400,
         detail="No paper loaded. Call /paper first."
      )

    try:
        # Trim history to last 6 messages
        trimmed_history = [
            {"role": m.role, "content": m.content}
            for m in request.history[-HISTORY_MESSAGES:]
        ]

        result = answer(
                question=request.question,
                arxiv_id=session["arxiv_id"],
                history=trimmed_history
        )

        source = None

        if result.source:
            source = SourceResponse(
               citations=[
                    Citation(quote=c.quote, section=c.section)
                    for c in result.source.citations
                ]
            )

        return ChatResponse(
            answer=result.answer,
            source=source,
            confidence=result.confidence
        )
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset():
    session["arxiv_id"] = None
    session["title"] = None
    session["summary"] = None
    session["suggested_questions"] = []
    return {"message": "Session reset successfully"}

@app.get("/session", response_model=SessionResponse)
async def get_session():
    return SessionResponse(
        arxiv_id=session["arxiv_id"],
        title=session["title"],
        summary=session["summary"],
        suggested_questions=session["suggested_questions"]
    )