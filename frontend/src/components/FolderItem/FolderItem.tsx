import {
  Folder,
  X,
  CheckCircle2,
  ChevronDown,
  FileText,
  FileAudio,
  Image,
  FileType,
  File,
} from "lucide-react";
import { useState } from "react";
import { FolderItemProps } from "./types";
import { Button } from "../ui/button";
import { useApp } from "@/context/AppContext";

const textExtensions = [".txt", ".md", ".json", ".xml", ".csv", ".html", ".css", ".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".c", ".cpp", ".h", ".rb", ".go", ".rs", ".swift", ".kt", ".sh", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".log"];
const audioExtensions = [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".aiff"];
const imageExtensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".heic"];
const pdfExtensions = [".pdf"];

function getFileIcon(fileName: string) {
  const ext = fileName.toLowerCase().slice(fileName.lastIndexOf("."));

  if (textExtensions.includes(ext)) {
    return <FileText className="h-3 w-3 text-blue-500 shrink-0" />;
  }
  if (audioExtensions.includes(ext)) {
    return <FileAudio className="h-3 w-3 text-purple-500 shrink-0" />;
  }
  if (imageExtensions.includes(ext)) {
    return <Image className="h-3 w-3 text-green-500 shrink-0" />;
  }
  if (pdfExtensions.includes(ext)) {
    return <FileType className="h-3 w-3 text-red-500 shrink-0" />;
  }
  return <File className="h-3 w-3 text-zinc-400 shrink-0" />;
}

export function FolderItem({ folder, onRemove }: FolderItemProps) {
  const { isGeneratingEmbeddings, handleFileClick } = useApp();
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFileItemClick = (fileName: string) => {
    const filePath = `${folder.path}/${fileName}`;
    handleFileClick(filePath, fileName);
  };

  return (
    <div className="w-full">
      <div
        className={` flex w-full items-center justify-between gap-2 rounded-lg border p-2 pl-4 pr-2 text-sm transition-colors`}
      >
        <div className="flex items-center gap-2 flex-1">
          {folder.processed && (
            <div title="Processed">
              <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
            </div>
          )}
          <Folder className={`h-4 w-4`} />
          <span className={``}>{folder.name}</span>
          {folder.files.length > 0 && (
            <span className="text-xs text-zinc-500">
              ({folder.files.length})
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {folder.files.length > 0 && (
            <Button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center justify-center rounded p-1 hover:bg-zinc-100 transition-colors"
              title={isExpanded ? "Collapse" : "Expand"}
              variant={"ghost"}
              size={null}
            >
              <ChevronDown
                className={`h-4 w-4 text-zinc-400 transition-transform ${
                  isExpanded ? "rotate-180" : ""
                }`}
              />
            </Button>
          )}
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
      </div>

      {/* Expandable files dropdown */}
      <div
        className={`overflow-hidden transition-all duration-200 ease-in-out ${
          isExpanded ? "max-h-96" : "max-h-0"
        }`}
      >
        <div className="border border-t-0 border-zinc-200 rounded-b-lg bg-zinc-50 p-3 ml-2 mr-2 mb-1">
          <div className="space-y-1">
            {folder.files.map((file) => (
              <button
                key={file}
                onClick={() => handleFileItemClick(file)}
                className="w-full text-left text-xs text-zinc-700 flex items-center gap-2 py-1 px-2 rounded hover:bg-zinc-200 cursor-pointer transition-colors"
              >
                {getFileIcon(file)}
                <span className="truncate">{file}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
