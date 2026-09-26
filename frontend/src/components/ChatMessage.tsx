import type { ChatMessage as ChatMessageType } from "../types"
import CitationList from "./CitationList"
import ConfidenceBadge from "./ConfidenceBadge"

interface ChatMessageProps {
    message: ChatMessageType
}

const ChatMessage = ({ message }: ChatMessageProps) => {
    const isUser = message.role === "user"

    return (
        <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
            <div
                className={isUser ? "max-w-[80%] rounded-2xl px-4 py-3 bg-gray-100 text-gray-900" : ""}
            >
                <p className="text-sm">{message.content}</p>

                {!isUser && message.source && (
                    <CitationList source={message.source} />
                )}

                {!isUser && message.confidence && (
                    <div className="mt-2">
                        <ConfidenceBadge confidence={message.confidence} />
                    </div>
                )}
            </div>
        </div>
    )
}

export default ChatMessage