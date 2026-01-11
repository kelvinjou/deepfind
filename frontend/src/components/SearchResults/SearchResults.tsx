import { SearchResultItem } from "@/components/SearchResultItem/SearchResultItem"
import { SearchResultsProps } from "./types"

export function SearchResults({
  results,
  onFileClick,
  onApproveMove,
  onApproveCopy,
}: SearchResultsProps) {
  const showMoveApprove =
    results.confirm_required &&
    results.pending_actions?.move_files?.action === "move_files";
  const showCopyApprove =
    results.confirm_required &&
    results.pending_actions?.copy_files?.action === "copy_files";

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
              showMoveApprove={showMoveApprove}
              onApproveMove={onApproveMove}
              showCopyApprove={showCopyApprove}
              onApproveCopy={onApproveCopy}
            />
          ))
        ) : (
          <p className="text-center text-zinc-500">No results found</p>
        )}
      </div>
    </div>
  )
}
