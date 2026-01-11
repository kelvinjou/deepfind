import { EmbeddingResult } from "@/types/app"

interface EmbeddingResultsProps {
  embeddingResults: EmbeddingResult[]
}

export function EmbeddingResults({ embeddingResults }: EmbeddingResultsProps) {
  if (embeddingResults.length === 0) return null

  const result = embeddingResults[0]

  return (
    <div className="mt-6 w-full max-w-md text-left">
      <h3 className="text-sm font-semibold text-zinc-700 mb-3">Embedding Results</h3>
      <div className="rounded-lg border bg-white p-4 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <div
            className={`h-3 w-3 rounded-full ${
              result?.data?.status === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm font-medium text-zinc-700">
            Status: {result?.data?.status === 'success' ? 'Success' : 'Failed'}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-md bg-zinc-50 p-3">
            <p className="text-zinc-500 text-xs">Processed</p>
            <p className="text-xl font-semibold text-zinc-800">
              {result?.data?.processedCount ?? 0}
            </p>
          </div>
          <div className="rounded-md bg-zinc-50 p-3">
            <p className="text-zinc-500 text-xs">Total Attempted</p>
            <p className="text-xl font-semibold text-zinc-800">
              {result?.data?.totalAttempted ?? 0}
            </p>
          </div>
        </div>
        {result?.data?.failedFiles && result.data.failedFiles.length > 0 && (
          <div className="rounded-md bg-red-50 p-3">
            <p className="text-red-600 text-xs font-medium mb-1">
              Failed Files ({result.data.failedFiles.length})
            </p>
            <ul className="text-xs text-red-700 space-y-1">
              {result.data.failedFiles.map((file: string, i: number) => (
                <li key={i} className="truncate">
                  {file}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
