interface ConfidenceBadgeProps {
    confidence: string | null
}

const ConfidenceBadge = ({ confidence }: ConfidenceBadgeProps) => {
    if (!confidence) return null

    const styles = {
        high: "bg-green-100 text-green-700",
        medium: "bg-yellow-100 text-yellow-700",
        low: "bg-red-100 text-red-700",
    }

    const style = styles[confidence as keyof typeof styles] ?? "bg-gray-100 text-gray-700"

    return (
        <span className={`text-xs font-medium px-2 py-1 rounded-full ${style}`}>
            {confidence} confidence
        </span>
    )
}

export default ConfidenceBadge