import useChat from "./hooks/useChat"
import PaperInput from "./components/PaperInput"
import ChatThread from "./components/ChatThread"
import InputChat from "./components/InputChat"
import SuggestedQuestions from "./components/SuggestedQuestions"
import Header from "./components/Header"

const App = () => {
  const { paper, messages, loading, error, submitQuestion, submitPaper, reset } = useChat()

  if (!paper) {
    return <PaperInput onSubmit={submitPaper} loading={loading} error={error} />
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto px-4">
      <Header
        paperTitle={paper.title}
        paperSummary={paper.summary}
        reset={reset}
      />

      <SuggestedQuestions
        suggestedQuestions={paper.suggested_questions}
        submitQuestion={submitQuestion} />

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