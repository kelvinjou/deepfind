import { FolderData } from "@/types/app"

export interface FolderItemProps {
  folder: FolderData
  index: number
  onToggle: (index: number) => void
  onRemove: (index: number) => void
}
