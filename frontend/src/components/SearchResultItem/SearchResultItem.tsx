import { Folder } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SearchResultItemProps } from "./types";

export function SearchResultItem({
  result,
  onClick,
  showMoveApprove,
  onApproveMove,
  showCopyApprove,
  onApproveCopy,
  tagLabel,
  tagColorClass,
}: SearchResultItemProps) {
  return (
    <div className="w-full rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow text-left">
      <button
        onClick={() => onClick(result.file_path, result.file_name)}
        className="w-full text-left"
      >
        <div className="flex items-start gap-3">
          <Folder className="h-5 w-5 text-zinc-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-zinc-800">{result.file_name}</h3>
            {tagLabel && (
              <div className="mt-2 inline-flex items-center gap-2 rounded-full border px-2 py-0.5 text-xs text-zinc-600">
                <span className={`h-2 w-2 rounded-full ${tagColorClass}`} />
                Tagged: {tagLabel}
              </div>
            )}
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
            </div>
          </div>
        </div>
      </button>
      {(showMoveApprove || showCopyApprove) && (
        <div className="mt-3 flex gap-2">
          {showMoveApprove && onApproveMove && (
            <Button onClick={onApproveMove} size="sm">
              Approve move
            </Button>
          )}
          {showCopyApprove && onApproveCopy && (
            <Button onClick={onApproveCopy} size="sm" variant="outline">
              Approve copy
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
