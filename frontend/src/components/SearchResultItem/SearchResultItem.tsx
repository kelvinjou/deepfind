import { Folder } from "lucide-react";
import { SearchResultItemProps } from "./types";

export function SearchResultItem({ result, onClick }: SearchResultItemProps) {
  // Format the last modified date
  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <button
      onClick={() => onClick(result.file_path, result.file_name)}
      className="w-full rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow text-left"
    >
      <div className="flex items-start gap-3">
        <Folder className="h-5 w-5 text-zinc-500 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-medium text-zinc-800">{result.file_name}</h3>
          <p className="text-sm text-zinc-500 mt-1">{result.file_path}</p>
          {result.content && (
            <p className="text-sm text-zinc-600 mt-2">{result.content}</p>
          )}
          <div className="flex items-center gap-4 mt-2">
            {result.similarity && (
              <p className="text-xs text-zinc-400">
                Similarity: {(result.similarity * 100).toFixed(1)}%
              </p>
            )}
            {result.similarity && result.last_modified_at && (
              <span className="text-zinc-300">|</span>
            )}
            {result.last_modified_at && (
              <p className="text-xs text-zinc-400">
                Modified: {formatDate(result.last_modified_at)}
              </p>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}
