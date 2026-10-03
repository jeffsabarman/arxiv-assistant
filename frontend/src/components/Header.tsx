import ReactMarkdown from "react-markdown"
import Accordion from "./shared/Accordion"

interface HeaderProps {
    paperTitle: string,
    paperSummary: string,
    reset: () => void
}

const Header = ({ paperTitle, paperSummary, reset }: HeaderProps) => {

    return (
        <div className="flex items-start justify-between py-4 border-b-gray-200">
            <Accordion
                title={
                    <h1 className="font-semibold text-sm max-w-md text-left">{paperTitle}</h1>
                }
                defaultOpen={true}
            >
                <div className="text-xs text-gray-500 prose prose-sm max-w-none">
                    <ReactMarkdown>
                        {paperSummary}
                    </ReactMarkdown>
                </div>
            </Accordion>
            <button
                onClick={reset}
                className="text-xs bg-black text-white rounded-full px-3 py-1.5 hover:opacity-80 ml-4 shrink-0 cursor-pointer"
            >
                Load new paper
            </button>
        </div>
    )
}

export default Header