import { useApp } from "@/context/AppContext"
import { EmptyState } from "@/components/EmptyState/EmptyState"
import { LoadingState } from "@/components/LoadingState/LoadingState"
import { ErrorState } from "@/components/ErrorState/ErrorState"
import { FilePreview } from "@/components/FilePreview/FilePreview"
import { SearchResults } from "@/components/SearchResults/SearchResults"

export function MainContent() {
  const {
    results,
    loading,
    error,
    selectedFile,
    isGeneratingEmbeddings,
    handleFileClick,
    handleCloseFile,
  } = useApp()

  const showEmptyState = !results && !loading && !error

  return (
    <div
      className={`flex flex-1 flex-col items-center p-8 overflow-y-auto ${
        showEmptyState ? 'justify-center' : 'justify-start'
      }`}
    >
      {showEmptyState && <EmptyState />}

      {(loading || isGeneratingEmbeddings) && (
        <LoadingState isGeneratingEmbeddings={isGeneratingEmbeddings} />
      )}

      {error && <ErrorState error={error} />}

      {selectedFile ? (
        <FilePreview file={selectedFile} onClose={handleCloseFile} />
      ) : (
        results && <SearchResults results={results} onFileClick={handleFileClick} />
      )}
    </div>
  )
}
