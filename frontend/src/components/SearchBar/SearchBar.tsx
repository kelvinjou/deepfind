import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Sparkles } from "lucide-react"
import { useApp } from "@/context/AppContext"

export function SearchBar() {
  const {
    query,
    setQuery,
    isSearchDisabled,
    embeddingsGenerated,
    handleSearch,
    preprocess,
  } = useApp()

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  return (
    <div className="flex items-center gap-3 border-b bg-white px-6 py-4">
      <Button onClick={preprocess}>
        <Sparkles />
      </Button>
      <Input
        placeholder={embeddingsGenerated ? "Search" : "Generate embeddings first to search"}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={isSearchDisabled}
        onKeyDown={handleKeyDown}
        className="flex-1 border-1 shadow-none focus-visible:ring-0"
      />
      <Search className="h-5 w-5 text-zinc-400" />
    </div>
  )
}
