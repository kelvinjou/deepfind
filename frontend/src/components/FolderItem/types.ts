import { FolderData } from "@/types/app";

export interface FolderItemProps {
  folder: FolderData;
  onRemove: (folder: FolderData) => void;
}
