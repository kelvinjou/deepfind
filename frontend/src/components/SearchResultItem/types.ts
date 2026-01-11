import { SearchResult } from "@/types/app"

export interface SearchResultItemProps {
  result: SearchResult
  onClick: (filePath: string, fileName: string) => void
  showMoveApprove?: boolean
  onApproveMove?: () => void
  showCopyApprove?: boolean
  onApproveCopy?: () => void
  tagLabel?: string
  tagColorClass?: string
}
