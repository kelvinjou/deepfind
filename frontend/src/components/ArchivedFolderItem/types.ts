import { FolderData } from "@/types/app";

export interface ArchivedFolderItemProps {
  folder: FolderData;
  onUnarchive: (folder: FolderData) => void;
  onDelete: (folder: FolderData) => void;
}
