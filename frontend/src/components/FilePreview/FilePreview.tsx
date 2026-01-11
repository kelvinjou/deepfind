import { Button } from "@/components/ui/button";
import { X, Sparkles } from "lucide-react";
import { FilePreviewProps } from "./types";
import { useEffect, useState } from "react";
import { useApp } from "@/context/AppContext";

function getFileType(filename: string): "text" | "image" | "pdf" | "audio" {
  const ext = filename.split(".").pop()?.toLowerCase() || "";

  if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext)) {
    return "image";
  }
  if (ext === "pdf") {
    return "pdf";
  }
  if (["mp3", "wav", "ogg", "m4a", "aac", "flac"].includes(ext)) {
    return "audio";
  }
  return "text";
}

export function FilePreview({ file, onClose }: FilePreviewProps) {
  const { summarizeFile, isAgentRunning } = useApp();
  const fileType = getFileType(file.name);
  const [dataUrl, setDataUrl] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  const handleSummarize = () => {
    // For text files, we can pass content directly
    // For other file types, we pass the file path and let the backend extract content
    if (fileType === "text" && file.content) {
      summarizeFile(file.name, file.path, file.content);
    } else {
      summarizeFile(file.name, file.path);
    }
  };

  // Can summarize all file types
  const canSummarize = true;

  // Load binary files as data URLs via IPC
  useEffect(() => {
    if (fileType === "text") {
      setLoading(false);
      return;
    }

    const loadFile = async () => {
      try {
        setLoading(true);
        const url = await window.electronAPI.readFileAsDataUrl(file.path);
        setDataUrl(url);
        setError("");
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load file";
        setError(message);
        setDataUrl("");
      } finally {
        setLoading(false);
      }
    };

    loadFile();
  }, [file.path, fileType]);

  return (
    <div className="w-full max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-zinc-800">{file.name}</h2>
        <div className="flex items-center gap-2">
          {canSummarize && (
            <Button
              onClick={handleSummarize}
              variant="default"
              size="sm"
              disabled={isAgentRunning}
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Summarize
            </Button>
          )}
          <Button onClick={onClose} variant="outline" size="sm">
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
        </div>
      </div>
      <p className="text-sm text-zinc-500 mb-4">{file.path}</p>
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        {fileType === "text" && (
          <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-800 overflow-auto max-h-[60vh]">
            {file.content}
          </pre>
        )}

        {fileType === "image" && loading && (
          <div className="flex justify-center items-center h-64 text-zinc-500">
            Loading image...
          </div>
        )}

        {fileType === "image" && !loading && error && (
          <div className="flex justify-center items-center h-64 text-red-500">
            {error}
          </div>
        )}

        {fileType === "image" && !loading && dataUrl && (
          <div className="flex justify-center items-center">
            <img
              src={dataUrl}
              alt={file.name}
              className="max-w-full max-h-[60vh] object-contain rounded"
            />
          </div>
        )}

        {fileType === "audio" && loading && (
          <div className="flex justify-center items-center h-20 text-zinc-500">
            Loading audio...
          </div>
        )}

        {fileType === "audio" && !loading && error && (
          <div className="flex justify-center items-center h-20 text-red-500">
            {error}
          </div>
        )}

        {fileType === "audio" && !loading && dataUrl && (
          <div className="flex flex-col items-center gap-4">
            <audio controls className="w-full max-w-md" src={dataUrl}>
              Your browser does not support the audio element.
            </audio>
          </div>
        )}

        {fileType === "pdf" && loading && (
          <div className="flex justify-center items-center h-96 text-zinc-500">
            Loading PDF...
          </div>
        )}

        {fileType === "pdf" && !loading && error && (
          <div className="flex justify-center items-center h-96 text-red-500">
            {error}
          </div>
        )}

        {fileType === "pdf" && !loading && dataUrl && (
          <div className="flex flex-col items-center gap-4">
            <iframe
              src={dataUrl}
              className="w-full rounded"
              style={{ height: "60vh" }}
              title={file.name}
            />
            <p className="text-sm text-zinc-500">
              If PDF doesn't display, download to view: {file.name}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
