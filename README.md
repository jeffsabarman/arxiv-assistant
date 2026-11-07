# ArXiv Paper Assistant

Chat with any ArXiv paper. Paste a link, get a summary and suggested questions, then ask follow-ups and get answers with cited sections.

**Status:** In development.

## Features

- **Section-aware parsing:** uses ArXiv's HTML version instead of PDF, so section hierarchy is preserved and every chunk carries its section name.
- **Multi-query retrieval:** an LLM rewrites each question into several variants using the paper's abstract, which fixes the mismatch between how people ask and how papers are written.
- **Agent with tool calling:** a PydanticAI agent decides when to search the paper and when to answer directly.
- **Streaming answers:** Server-Sent Events from FastAPI, read with `fetch` and `ReadableStream`.
- **Citations and confidence:** answers show the sections they draw on, plus a high/medium/low confidence score based on vector distances.
- **Conversation history:** trimmed to the last 6 messages to control token cost.

## Architecture

```
React (Vite) ── fetch / SSE ──> FastAPI
                                  │
                                  ├─ paper.py     fetch + parse ArXiv HTML
                                  ├─ chunker.py   split into section-aware chunks
                                  ├─ embedder.py  OpenAI embeddings -> ChromaDB
                                  └─ rag.py       PydanticAI agent + search_paper tool
```

Request flow for a question: the agent reads the paper context, decides whether to call `search_paper`, which rewrites the query into variants, searches ChromaDB, and returns the merged chunks. The answer streams back, then citations and confidence arrive in a final event.

## Tech stack

- **Backend:** Python 3.11, FastAPI, Pydantic, PydanticAI
- **AI:** GPT-4o, `text-embedding-3-small`
- **Retrieval:** ChromaDB (persistent), LangChain `RecursiveCharacterTextSplitter`, BeautifulSoup
- **Frontend:** React, TypeScript, Vite, Tailwind CSS v4, Radix UI

## Getting started

**Prerequisites:** Python 3.11, Node 20+, an OpenAI API key.

```bash
# backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
uvicorn main:app --reload
```

```bash
# frontend
cd frontend
npm install
cp .env.example .env        # VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173 and paste an ArXiv link, for example `arxiv.org/abs/1706.03762`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/paper` | Fetch, chunk and embed a paper, return summary and suggested questions |
| POST | `/chat/stream` | Stream an answer, then citations and confidence |
| GET | `/session` | Current paper state |
| POST | `/reset` | Clear the session |

## Design decisions

- **HTML over PDF:** `<section>` tags give reliable section boundaries and hierarchy.
- **Citations built in code:** chunks retrieved by the search are ranked by word overlap with the answer, so quotes are always real text from the paper. The trade-off is that they show what was retrieved, not what the model verified it used.
- **Plain-text streaming:** structured output delivered the whole answer in one piece, so the agent streams plain text and citations are attached afterwards.
- **Persistent ChromaDB:** papers survive restarts, so a paper is only embedded once.

## Current limitations

- One shared session for all users (single in-memory session), so it's meant for single-user demos.
- Time to first token on paper questions includes query rewriting and retrieval.
- Citations are word-overlap based, not semantic.

## Roadmap

- [ ] Docker and docker-compose
- [ ] GitHub Actions CI/CD
- [ ] Per-user sessions and rate limiting
- [ ] Model-chosen citations
- [ ] Corrective retrieval loop (retrieve, grade, rewrite)
- [ ] Chat persistence