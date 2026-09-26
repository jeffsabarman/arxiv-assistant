import type { SourceResponse } from "../types"

interface CitationListProps {
    source: SourceResponse
}

const CitationList = ({ source }: CitationListProps) => {
    if (!source.citations.length) return null

    return (
        <div className="mt-3 flex flex-col gap-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Citations
            </p>
            {source.citations.map((citation, index) => (
                <div
                    key={index}
                    className="border-l-2 border-gray-200 pl-3 flex flex-col gap-1"
                >
                    <p className="text-xs text-gray-500 font-medium">{citation.section}</p>
                    <p className="text-xs text-gray-600 italic">"{citation.quote}"</p>
                </div>
            ))}
        </div>
    )
}

export default CitationList