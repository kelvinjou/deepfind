import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { useApp } from "@/context/AppContext"
import { EmbeddingResults } from "@/components/EmbeddingResults/EmbeddingResults"

export function EmptyState() {
  const { handleSelectFolder, embeddingResults } = useApp()

  return (
    <div className="text-center">
      <Button
        onClick={handleSelectFolder}
        className="flex items-center gap-2 text-lg"
        size="lg"
      >
        <Plus className="h-5 w-5" />
        Add new folder
      </Button>
      <p className="mt-4 text-center text-sm text-zinc-500">
        Add folders to search through your files
      </p>
      <EmbeddingResults embeddingResults={embeddingResults} />
    </div>
  )
}
