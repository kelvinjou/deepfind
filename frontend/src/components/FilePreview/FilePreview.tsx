import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { FilePreviewProps } from "./types"

export function FilePreview({ file, onClose }: FilePreviewProps) {
  return (
    <div className="w-full max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-zinc-800">{file.name}</h2>
        <Button onClick={onClose} variant="outline" size="sm">
          <X className="h-4 w-4 mr-2" />
          Close
        </Button>
      </div>
      <p className="text-sm text-zinc-500 mb-4">{file.path}</p>
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-800 overflow-auto max-h-[60vh]">
          {file.content}
        </pre>
      </div>
    </div>
  )
}
