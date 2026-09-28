import { useState } from "react"

interface PaperInputProps {
  onSubmit: (url: string) => void
  loading: boolean
  error: string | null
}

const PaperInput = ({ onSubmit, loading, error }: PaperInputProps) => {
  const [url, setUrl] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) onSubmit(url.trim())
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="w-full max-w-xl">
        <h1 className="text-3xl font-bold mb-2">ArXiv Assistant</h1>
        <p className="text-gray-500 mb-8">
          Paste an ArXiv paper URL to get started
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Paper URL</label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="e.g. arxiv.org/abs/1706.03762"
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-black"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="bg-black text-white rounded-lg px-4 py-3 text-sm font-medium cursor-pointer disabled:opacity-50 disabled:cursor-default"
          >
            {loading ? "Loading paper..." : "Load Paper"}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-sm text-red-500">{error}</p>
        )}
      </div>
    </div>
  )
}

export default PaperInput