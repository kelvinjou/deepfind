interface LoadingStateProps {
  isGeneratingEmbeddings: boolean
}

export function LoadingState({ isGeneratingEmbeddings }: LoadingStateProps) {
  return (
    <div className="text-center">
      <p className="text-lg text-zinc-600">
        {isGeneratingEmbeddings ? "Embedding..." : "Searching..."}
      </p>
    </div>
  )
}
