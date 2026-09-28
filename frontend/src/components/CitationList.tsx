import type { SourceResponse } from "../types"
import Accordion from "./shared/Accordion"

interface CitationListProps {
    source: SourceResponse
}

const CitationList = ({ source }: CitationListProps) => {

    if (!source.citations.length) return null

    return (
        <Accordion
            title={
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Citations ({source.citations.length})
                </span>
            }
        >
            {source.citations.map((citation, index) => (
                <div key={index} className="border-l-2 border-gray-200 pl-3 flex flex-col gap-1 mb-2">
                    <p className="text-xs text-gray-500 font-medium">{citation.section}</p>
                    <p className="text-xs text-gray-600 italic">"{citation.quote}"</p>
                </div>
            ))}
        </Accordion>
    )
}

export default CitationList