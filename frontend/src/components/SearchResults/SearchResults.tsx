import { SearchResultItem } from "@/components/SearchResultItem/SearchResultItem"
import { SearchResultsProps } from "./types"

export function SearchResults({ results, onFileClick }: SearchResultsProps) {
  return (
    <div className="w-full max-w-4xl">
      <h2 className="mb-4 text-xl font-semibold text-zinc-800">Search Results</h2>
      <div className="space-y-3 pb-8">
        {results.results && results.results.length > 0 ? (
          results.results.map((result, index) => (
            <SearchResultItem
              key={index}
              result={result}
              onClick={onFileClick}
            />
          ))
        ) : (
          <p className="text-center text-zinc-500">No results found</p>
        )}
      </div>
    </div>
  )
}
