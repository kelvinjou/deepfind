import { useApp } from "@/context/AppContext";
import { EmptyState } from "@/components/EmptyState/EmptyState";
import { FilePreview } from "@/components/FilePreview/FilePreview";
import { SearchResults } from "@/components/SearchResults/SearchResults";

export function MainContent() {
  const {
    results,
    loading,
    selectedFile,
    handleFileClick,
    handleCloseFile,
  } = useApp();

  const showEmptyState = !results && !loading;

  return (
    <div
      className={`flex flex-1 flex-col items-center p-8 overflow-y-auto ${
        showEmptyState ? "justify-center" : "justify-start"
      }`}
    >
      {showEmptyState && <EmptyState />}

      {selectedFile ? (
        <FilePreview file={selectedFile} onClose={handleCloseFile} />
      ) : (
        results && (
          <SearchResults results={results} onFileClick={handleFileClick} />
        )
      )}
    </div>
  );
}
