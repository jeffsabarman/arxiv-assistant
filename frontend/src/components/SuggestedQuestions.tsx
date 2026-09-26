
interface SuggestedQuestionsProps {
    suggestedQuestions: string[],
    submitQuestion: (question: string) => void
}

const SuggestedQuestions = ({ suggestedQuestions, submitQuestion }: SuggestedQuestionsProps) => {

    return (
        <div className="flex flex-col gap-2 py-6">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                Suggested questions
            </p>
            <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((q, i) => (
                    <button
                        key={i}
                        onClick={() => submitQuestion(q)}
                        className="text-xs text-left border border-gray-200 rounded-full px-3 py-1.5 hover:bg-gray-50 hover:cursor-pointer"
                    >
                        {q}
                    </button>
                ))}
            </div>
        </div>
    )
}

export default SuggestedQuestions