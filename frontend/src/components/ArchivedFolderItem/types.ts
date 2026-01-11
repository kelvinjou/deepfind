import { FolderData } from "@/types/app";

export interface ArchivedFolderItemProps {
  folder: FolderData;
  index: number;
  onUnarchive: (index: number) => void;
  onDelete: (index: string) => void;
}
