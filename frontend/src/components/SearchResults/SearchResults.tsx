import { SearchResultItem } from "@/components/SearchResultItem/SearchResultItem"
import { SearchResultsProps } from "./types"

export function SearchResults({
  results,
  onFileClick,
  onApproveMove,
  onApproveCopy,
  onSelectTagColor,
}: SearchResultsProps) {
  const tagInfo = getTagInfo(results.tag_color);
  const showMoveApprove =
    results.confirm_required &&
    results.pending_actions?.move_files?.action === "move_files";
  const showCopyApprove =
    results.confirm_required &&
    results.pending_actions?.copy_files?.action === "copy_files";
  const showTagPicker =
    results.action === "tag_files" &&
    results.confirm_required &&
    results.pending_actions?.tag_files?.action === "tag_files";

  return (
    <div className="w-full max-w-4xl">
      <h2 className="mb-4 text-xl font-semibold text-zinc-800">Search Results</h2>
      {results.action === "tag_files" && (
        <div className="mb-4 rounded-lg border bg-white px-4 py-3 text-sm text-zinc-700">
          {showTagPicker ? (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${tagInfo.className}`} />
                <span>
                  Select a tag color for “{results.tag ?? "tagged"}” ({results.taggable_count ?? 0} file
                  {(results.taggable_count ?? 0) === 1 ? "" : "s"})
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {TAG_COLORS.map((color) => (
                  <button
                    key={color.value}
                    type="button"
                    onClick={() => onSelectTagColor?.(color.value)}
                    className="flex items-center gap-2 rounded-md border px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                  >
                    <span className={`h-2.5 w-2.5 rounded-full ${color.className}`} />
                    {color.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${tagInfo.className}`} />
              <span>
                Tagged {results.tagged_count ?? 0} file
                {(results.tagged_count ?? 0) === 1 ? "" : "s"} with “{results.tag ?? "tagged"}”
                {tagInfo.label ? ` (${tagInfo.label})` : ""}
              </span>
            </div>
          )}
        </div>
      )}
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
              tagLabel={
                results.action === "tag_files" && !showTagPicker
                  ? results.tag
                  : undefined
              }
              tagColorClass={
                results.action === "tag_files" && !showTagPicker
                  ? tagInfo.className
                  : undefined
              }
            />
          ))
        ) : (
          <p className="text-center text-zinc-500">No results found</p>
        )}
      </div>
    </div>
  )
}

function getTagInfo(color?: number) {
  switch (color) {
    case 1:
      return { label: "gray", className: "bg-zinc-400" };
    case 2:
      return { label: "green", className: "bg-green-500" };
    case 3:
      return { label: "purple", className: "bg-purple-500" };
    case 4:
      return { label: "blue", className: "bg-blue-500" };
    case 5:
      return { label: "yellow", className: "bg-yellow-400" };
    case 6:
      return { label: "red", className: "bg-red-500" };
    case 7:
      return { label: "orange", className: "bg-orange-500" };
    default:
      return { label: null, className: "bg-zinc-300" };
  }
}

const TAG_COLORS = [
  { label: "Gray", value: 1, className: "bg-zinc-400" },
  { label: "Green", value: 2, className: "bg-green-500" },
  { label: "Purple", value: 3, className: "bg-purple-500" },
  { label: "Blue", value: 4, className: "bg-blue-500" },
  { label: "Yellow", value: 5, className: "bg-yellow-400" },
  { label: "Red", value: 6, className: "bg-red-500" },
  { label: "Orange", value: 7, className: "bg-orange-500" },
];
