export type FileType = "text" | "audio" | "image" | "pdf";

export interface FolderData {
  path: string;
  name: string;
  processed: boolean;
  archived: boolean;
  files: string[];
}

export interface SelectedFile {
  path: string;
  content: string;
  name: string;
}

export interface SearchResult {
  file_name: string;
  file_path: string;
  content?: string;
  similarity?: number;
  last_modified_at?: string;
}

export interface SearchResults {
  results: SearchResult[];
}

export interface EmbeddingResult {
  data?: {
    status: string;
    processedCount?: number;
    totalAttempted?: number;
    failedFiles?: string[];
  };
}

export interface File {
  id: string;
  file_path: string;
  file_name: string;
  file_type: string;
  file_size: number | null;
  mime_type: string;
  file_hash: string;
  last_modified_at: string;
  uploaded_at: string | null;
  processed_at: string | null;
  processing_status: string | null;
  metadata: Record<string, unknown>;
}

export interface Chunk {
  id: string;
  file_id: string;
  chunk_index: number;
  content: string;
  embedding: number[] | null;
  chunk_metadata: Record<string, unknown>;
  created_at: string | null;
}
