import { Folder, RotateCcw, Trash2 } from "lucide-react";
import { ArchivedFolderItemProps } from "./types";
import { Button } from "../ui/button";

export function ArchivedFolderItem({
  folder,
  onUnarchive,
  onDelete,
}: ArchivedFolderItemProps) {
  return (
    <div className="flex w-full items-center justify-between gap-2 rounded-lg border border-zinc-300 bg-zinc-50 p-2 pl-4 pr-2 text-sm transition-colors">
      <div className="flex items-center gap-2 text-zinc-500">
        <Folder className="h-4 w-4" />
        <span className="text-zinc-600">{folder.name}</span>
      </div>
      <div className="flex gap-1">
        <Button
          onClick={() => onUnarchive(folder)}
          className="flex items-center justify-center"
          title="Restore to active folders"
          variant="ghost"
          size="icon-sm"
        >
          <RotateCcw className="h-4 w-4 text-blue-600" />
        </Button>
        <Button
          onClick={() => onDelete(folder)}
          className="flex items-center justify-center"
          title="Permanently delete"
          variant="ghost"
          size="icon-sm"
        >
          <Trash2 className="h-4 w-4 text-red-600" />
        </Button>
      </div>
    </div>
  );
}
