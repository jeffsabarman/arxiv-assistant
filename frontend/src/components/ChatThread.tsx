import type { ChatMessage as ChatMessageType } from "../types"
import ChatMessage from "./ChatMessage"

const TypingIndicator = () => {
    return (
        <div className="flex justify-start">
            {/* <div className="bg-gray-100 rounded-2xl px-4 py-3"> */}
            <div className="flex gap-1 items-center h-4">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
            {/* </div> */}
        </div>
    )
}

interface ChatThreadProps {
    messages: ChatMessageType[]
    loading: boolean
}

const ChatThread = ({ messages, loading }: ChatThreadProps) => {
    return (
        <div className="flex flex-col gap-4 p-4 pt-2">
            {messages.map((message, index) => (
                <ChatMessage key={index} message={message} />
            ))}

            {loading && <TypingIndicator />}
        </div>
    )
}

export default ChatThread