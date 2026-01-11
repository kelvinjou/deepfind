import { Button } from "@/components/ui/button";
import { X, Loader2, FileText } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { useEffect, useRef } from "react";

export function OutputPanel() {
  const {
    agentOutput,
    agentMetadata,
    isAgentRunning,
    showOutputPanel,
    closeOutputPanel,
  } = useApp();

  const outputRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom as new content streams in
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [agentOutput]);

  if (!showOutputPanel) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-zinc-800">Agent Output</h2>
          {isAgentRunning && (
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          )}
        </div>
        <Button onClick={closeOutputPanel} variant="outline" size="sm">
          <X className="h-4 w-4 mr-2" />
          Close
        </Button>
      </div>

      {agentMetadata && (
        <div className="mb-4 flex flex-wrap items-center gap-4 text-sm text-zinc-600">
          {agentMetadata.topic && (
            <span className="flex items-center gap-1">
              <span className="font-medium">Topic:</span> {agentMetadata.topic}
            </span>
          )}
          {agentMetadata.fileType && (
            <span className="flex items-center gap-1 px-2 py-0.5 bg-zinc-100 rounded text-xs">
              {agentMetadata.fileType}
            </span>
          )}
          {agentMetadata.documentsFound !== undefined && (
            <span className="flex items-center gap-1">
              <FileText className="h-4 w-4" />
              <span className="font-medium">{agentMetadata.documentsFound}</span> documents found
            </span>
          )}
        </div>
      )}

      <div className="rounded-lg border bg-white shadow-sm">
        <div
          ref={outputRef}
          className="p-6 overflow-auto max-h-[60vh] min-h-[200px]"
        >
          {agentOutput ? (
            <div className="prose prose-zinc max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm text-zinc-800 leading-relaxed">
                {agentOutput}
              </pre>
            </div>
          ) : isAgentRunning ? (
            <div className="flex items-center justify-center h-32 text-zinc-500">
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span>Searching and synthesizing documents...</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-32 text-zinc-400">
              No output yet
            </div>
          )}
        </div>

        {!isAgentRunning && agentOutput && (
          <div className="border-t px-6 py-3 bg-zinc-50 rounded-b-lg">
            <span className="text-xs text-zinc-500">
              Generation complete
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
