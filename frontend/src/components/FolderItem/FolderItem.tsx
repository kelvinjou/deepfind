import { Folder, Check, X } from "lucide-react"
import { FolderItemProps } from "./types"

export function FolderItem({ folder, index, onToggle, onRemove }: FolderItemProps) {
  return (
    <div
      className={`flex w-full items-center gap-2 rounded-lg border p-3 text-sm transition-colors ${
        folder.selected
          ? "border-blue-500 bg-blue-50"
          : "bg-white"
      }`}
    >
      <button
        onClick={() => onToggle(index)}
        className="flex flex-1 items-center gap-2 hover:opacity-80"
      >
        <div
          className={`flex h-5 w-5 items-center justify-center rounded border ${
            folder.selected
              ? "border-blue-500 bg-blue-500"
              : "border-zinc-300 bg-white"
          }`}
        >
          {folder.selected && <Check className="h-3 w-3 text-white" />}
        </div>
        <Folder className={`h-4 w-4 ${folder.selected ? "text-blue-600" : "text-zinc-500"}`} />
        <span className={`truncate ${folder.selected ? "text-blue-900" : "text-zinc-700"}`}>
          {folder.path.split('/').pop()}
        </span>
      </button>
      <button
        onClick={() => onRemove(index)}
        className="flex items-center justify-center rounded p-1 hover:bg-red-100 transition-colors"
        title="Remove folder"
      >
        <X className="h-4 w-4 text-zinc-400 hover:text-red-600" />
      </button>
    </div>
  )
}
