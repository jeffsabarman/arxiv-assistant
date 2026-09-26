import { useRef, useState } from "react"
import type { ChatMessage, LoadPaperResponse } from "../types"
import { loadPaper, resetSession, sendChat } from "../api"

const useChat = () => {
  const [paper, setPaper] = useState<LoadPaperResponse | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submitPaper = async (url: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await loadPaper(url)
      setPaper(response)
      setMessages([])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load paper")
    } finally {
      setLoading(false)
    }
  }

  const submitQuestion = async (question: string) => {
    if (!paper) return

    const userMessage: ChatMessage = { role: "user", content: question }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)
    setError(null)

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))
      const response = await sendChat({ question, history })

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
        source: response.source,
        confidence: response.confidence,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message")
    } finally {
      setLoading(false)
    }
  }

  const reset = async () => {
    await resetSession()
    setPaper(null)
    setMessages([])
    setError(null)
  }

  return { paper, messages, loading, error, submitPaper, submitQuestion, reset }
}

export default useChat
