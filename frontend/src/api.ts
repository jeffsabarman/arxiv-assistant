import type { ChatRequest, ChatResponse, LoadPaperRequest, LoadPaperResponse, SessionResponse } from "./types"

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

async function handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
        const error = await res.json().catch(() => ({detail: "Unknown error"}))
        throw new Error(error.detail || "Request failed")
    }
    return res.json()
}

export async function loadPaper(url: string): Promise<LoadPaperResponse> {
    const res = await fetch(`${BASE_URL}/paper`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url} satisfies LoadPaperRequest)
    })
    return handleResponse<LoadPaperResponse>(res)
}

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
  return handleResponse<ChatResponse>(res)
}

export async function getSession(): Promise<SessionResponse> {
  const res = await fetch(`${BASE_URL}/session`)
  return handleResponse<SessionResponse>(res)
}

export async function resetSession(): Promise<void> {
  const res = await fetch(`${BASE_URL}/reset`, { method: "POST" })
  return handleResponse<void>(res)
}