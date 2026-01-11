import { SelectedFile } from "@/types/app"

export interface FilePreviewProps {
  file: SelectedFile
  onClose: () => void
}
