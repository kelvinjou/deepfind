import { useApp } from "@/context/AppContext";
import { EmptyState } from "@/components/EmptyState/EmptyState";
import { FilePreview } from "@/components/FilePreview/FilePreview";
import { SearchResults } from "@/components/SearchResults/SearchResults";
import { OutputPanel } from "@/components/OutputPanel/OutputPanel";

export function MainContent() {
  const {
    results,
    loading,
    selectedFile,
    handleFileClick,
    handleCloseFile,
    showOutputPanel,
  } = useApp();

  const showEmptyState = !results && !loading && !showOutputPanel;

  return (
    <div
      className={`flex flex-1 flex-col items-center p-8 overflow-y-auto ${
        showEmptyState ? "justify-center" : "justify-start"
      }`}
    >
      {showEmptyState && <EmptyState />}

      {showOutputPanel ? (
        <OutputPanel />
      ) : selectedFile ? (
        <FilePreview file={selectedFile} onClose={handleCloseFile} />
      ) : (
        results && (
          <SearchResults results={results} onFileClick={handleFileClick} />
        )
      )}
    </div>
  );
}
