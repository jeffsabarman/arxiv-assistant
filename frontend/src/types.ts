export interface Citation {
  quote: string
  section: string
}

export interface SourceResponse {
  citations: Citation[]
}

export interface LoadPaperRequest {
  url: string
}

export interface LoadPaperResponse {
  title: string
  summary: string
  suggested_questions: string[]
}

export interface ChatRequest {
  question: string
  history: { role: string; content: string }[]  // no arxiv_id
}

export interface ChatResponse {
  answer: string
  source: SourceResponse | null
  confidence: string | null
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  source?: SourceResponse | null
  confidence?: string | null
}

export interface SessionResponse {
  arxiv_id: string | null
  title: string | null
  summary: string | null
  suggested_questions: string[]
}