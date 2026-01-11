export interface FolderData {
  path: string;
  name: string;
  selected: boolean;
  processed: boolean;
  archived: boolean;
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
