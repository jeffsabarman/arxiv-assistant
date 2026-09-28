import useChat from "./hooks/useChat"
import PaperInput from "./components/PaperInput"
import ChatThread from "./components/ChatThread"
import InputChat from "./components/InputChat"
import SuggestedQuestions from "./components/SuggestedQuestions"

const App = () => {
  const { paper, messages, loading, error, submitQuestion, submitPaper, reset } = useChat()

  if (!paper) {
    return <PaperInput onSubmit={submitPaper} loading={loading} error={error} />
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto px-4">
      {/* Header */}
      <div className="flex items-center justify-between py-4 border-b-gray-200">
        <div>
          <h1 className="font-semibold text-sm truncate max-w-md">{paper.title}</h1>
          <p className="text-xs text-gray-500">{paper.summary}</p>
        </div>
        <button
          onClick={reset}
          className="text-xs bg-black text-white rounded-full px-3 py-1.5 hover:opacity-80 ml-4 shrink-0 cursor-pointer"
        >
          Load new paper
        </button>
      </div>

      {/* Suggested questions */}
      <SuggestedQuestions
        suggestedQuestions={paper.suggested_questions}
        submitQuestion={submitQuestion} />

      {/* Chat thread */}
      <div className="flex-1 overflow-y-auto">
        <ChatThread messages={messages} loading={loading} />
      </div>

      {/* Error */}
      {error && (
        <p className="text-xs text-red-500 pb-2">{error}</p>
      )}

      <div className="py-4">
        <InputChat submitQuestion={submitQuestion} loading={loading} />
      </div>

    </div>
  )
}

export default App