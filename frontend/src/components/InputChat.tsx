import { useState } from "react"
import { ArrowUp } from "lucide-react"

const textareaClass = [
    "w-full border border-gray-300 rounded-xl",
    "px-4 py-3 pr-12 text-sm",
    "focus:outline-none focus:border-gray-400",
    "resize-none disabled:opacity-50",
].join(" ")

interface InputChatProps {
    submitQuestion: (question: string) => void,
    loading: boolean
}

const InputChat = ({ submitQuestion, loading }: InputChatProps) => {
    // const { submitQuestion, loading } = useChat()
    const [question, setQuestion] = useState("")


    const handleSend = () => {
        const trimQuestion = question.trim()
        if (trimQuestion) {
            submitQuestion(trimQuestion)
            setQuestion("")
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="relative">
            <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about the paper..."
                rows={2}
                disabled={loading}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:shadow-md resize-none disabled:opacity-50"
            />
            <button
                onClick={handleSend}
                disabled={loading || !question.trim()}
                className="absolute right-3 bottom-4 bg-black text-white rounded-lg p-1.5 disabled:opacity-30 disabled:cursor-auto hover:cursor-pointer"
            >
                <ArrowUp size={16} strokeWidth={2.5} />
            </button>
        </div>
    )
}

export default InputChat