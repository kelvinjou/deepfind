import { SearchResult } from "@/types/app"

export interface SearchResultItemProps {
  result: SearchResult
  onClick: (filePath: string, fileName: string) => void
}
