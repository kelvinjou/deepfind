import { Folder, X, CheckCircle2 } from "lucide-react";
import { FolderItemProps } from "./types";
import { Button } from "../ui/button";
import { useApp } from "@/context/AppContext";

export function FolderItem({ folder, onRemove }: FolderItemProps) {
  const { isGeneratingEmbeddings } = useApp();
  return (
    <div
      className={` flex w-full items-center justify-between gap-2 rounded-lg border p-2 pl-4 pr-2 text-sm transition-colors`}
    >
      <div className="flex items-center gap-2">
        {folder.processed && (
          <div title="Processed">
            <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
          </div>
        )}
        <Folder className={`h-4 w-4`} />
        <span className={``}>{folder.name}</span>
      </div>
      <Button
        onClick={() => onRemove(folder)}
        className="flex items-center justify-center rounded p-1 group hover:bg-red-100 transition-colors"
        title="Remove folder"
        variant={"ghost"}
        size={null}
        disabled={isGeneratingEmbeddings}
      >
        <X className="h-4 w-4 text-zinc-400 group-hover:text-red-600" />
      </Button>
    </div>
  );
}
