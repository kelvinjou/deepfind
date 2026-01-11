interface ErrorStateProps {
  error: string
}

export function ErrorState({ error }: ErrorStateProps) {
  return (
    <div className="text-center">
      <p className="text-lg text-red-600">Error: {error}</p>
    </div>
  )
}
