import { SearchResults as SearchResultsType } from "@/types/app"

export interface SearchResultsProps {
  results: SearchResultsType
  onFileClick: (filePath: string, fileName: string) => void
  onApproveMove?: () => void
  onApproveCopy?: () => void
}
