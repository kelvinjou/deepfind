import { createContext, useContext, useState, ReactNode } from "react";
import {
  FolderData,
  SelectedFile,
  SearchResults,
  EmbeddingResult,
} from "@/types/app";
import { toast } from "sonner";

interface AppContextType {
  // Folder state
  folders: FolderData[];
  setFolders: React.Dispatch<React.SetStateAction<FolderData[]>>;

  // Search state
  query: string;
  setQuery: React.Dispatch<React.SetStateAction<string>>;
  results: SearchResults | null;
  setResults: React.Dispatch<React.SetStateAction<SearchResults | null>>;

  // UI state
  sidebarOpen: boolean;
  setSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>;
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;

  // File preview state
  selectedFile: SelectedFile | null;
  setSelectedFile: React.Dispatch<React.SetStateAction<SelectedFile | null>>;

  // Embedding state
  embeddingsGenerated: boolean;
  setEmbeddingsGenerated: React.Dispatch<React.SetStateAction<boolean>>;
  embeddingResults: EmbeddingResult[];
  setEmbeddingResults: React.Dispatch<React.SetStateAction<EmbeddingResult[]>>;
  isGeneratingEmbeddings: boolean;
  setIsGeneratingEmbeddings: React.Dispatch<React.SetStateAction<boolean>>;

  // Computed values
  isSearchDisabled: boolean;
  hasUnprocessedSelectedFolders: boolean;

  // Actions
  handleSelectFolder: () => Promise<void>;
  toggleFolderSelection: (index: number) => void;
  archiveFolder: (index: number) => void;
  unarchiveFolder: (index: number) => void;
  permanentlyDeleteFolder: (folderPath: string) => Promise<void>;
  handleSearch: () => Promise<void>;
  handleFileClick: (filePath: string, fileName: string) => Promise<void>;
  handleCloseFile: () => void;
  preprocess: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [folders, setFolders] = useState<FolderData[]>([]);
  const [query, setQuery] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);
  const [embeddingsGenerated, setEmbeddingsGenerated] = useState(false);
  const [embeddingResults, setEmbeddingResults] = useState<EmbeddingResult[]>(
    []
  );
  const [isGeneratingEmbeddings, setIsGeneratingEmbeddings] = useState(false);

  const isSearchDisabled =
    folders.length === 0 ||
    folders.some((f) => !f.archived && f.selected && !f.processed);

  const hasUnprocessedSelectedFolders = folders.some(
    (f) => !f.archived && f.selected && !f.processed
  );

  const handleSelectFolder = async () => {
    const result = await window.electronAPI.openDirectory();
    if (!result.canceled) {
      const folderPath = result.filePaths[0];

      if (folders.some((folder) => folder.path === folderPath)) {
        toast.error("Folder already added", { richColors: true });
        return;
      }

      await window.electronAPI.readDirectory(folderPath);
      setFolders((prev) => [
        ...prev,
        {
          path: folderPath,
          selected: true,
          processed: false,
          archived: false,
          name: folderPath.split("/").pop() || folderPath,
        },
      ]);
    }
  };

  const toggleFolderSelection = (index: number) => {
    setFolders((prev) =>
      prev.map((folder, i) =>
        i === index ? { ...folder, selected: !folder.selected } : folder
      )
    );
  };

  const archiveFolder = (index: number) => {
    setFolders((prev) => {
      const folder = prev[index];

      // If folder hasn't been processed, remove it completely (no DB data to archive)
      if (!folder.processed) {
        return prev.filter((_, i) => i !== index);
      }

      // Otherwise, archive it (marks it to be excluded from queries)
      return prev.map((f, i) =>
        i === index ? { ...f, archived: true, selected: false } : f
      );
    });
  };

  const unarchiveFolder = (index: number) => {
    setFolders((prev) =>
      prev.map((folder, i) =>
        i === index ? { ...folder, archived: false, selected: true } : folder
      )
    );
  };

  const permanentlyDeleteFolder = async (folderPath: string) => {
    try {
      // Call backend to delete all files from this folder in the database
      const response = await fetch("http://localhost:7777/folder/", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ folderPath }),
      });

      if (!response.ok) {
        throw new Error(`Failed to delete folder: ${response.status}`);
      }

      const data = await response.json();
      console.log(`Deleted ${data.deletedCount} files from database`);

      // Remove folder from state after successful deletion
      setFolders((prev) => prev.filter((f) => f.path !== folderPath));
    } catch (err) {
      console.error("Error deleting folder:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Failed to delete folder: ${errorMessage}`, {
        richColors: true,
      });
    }
  };

  const getQueryResults = async () => {
    const selectedFolderPaths = folders
      .filter(
        (folder) => !folder.archived && folder.selected && folder.processed
      )
      .map((folder) => folder.path);

    const archivedFolderPaths = folders
      .filter((folder) => folder.archived)
      .map((folder) => folder.path);

    const params = new URLSearchParams({
      query_text: query,
    });

    if (selectedFolderPaths.length > 0) {
      params.append("folders", JSON.stringify(selectedFolderPaths));
    }

    if (archivedFolderPaths.length > 0) {
      params.append("archived_folders", JSON.stringify(archivedFolderPaths));
    }

    const response = await fetch(
      `http://localhost:7777/query?${params.toString()}`,
      {
        method: "GET",
      }
    );
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  };

  const handleSearch = async () => {
    setLoading(true);

    try {
      const data = await getQueryResults();
      setResults(data);
    } catch (err: unknown) {
      console.error("Search error:", err);
      const errorMessage = err instanceof Error ? err.message : "Search failed";
      toast.error(errorMessage, { richColors: true });
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = async (filePath: string, fileName: string) => {
    if (!fileName.endsWith(".txt")) {
      toast.error("Only .txt files can be previewed", { richColors: true });
      return;
    }

    try {
      const content = await window.electronAPI.readFile(filePath);
      setSelectedFile({
        path: filePath,
        content: content,
        name: fileName,
      });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Failed to read file: ${errorMessage}`, { richColors: true });
    }
  };

  const handleCloseFile = () => {
    setSelectedFile(null);
  };

  const preprocess = async () => {
    // Get selected folders that haven't been processed yet (excluding archived)
    let unprocessedFolders = folders.filter(
      (f) => !f.archived && f.selected && !f.processed
    );

    // If no folders are selected, get all unprocessed folders (excluding archived)
    if (unprocessedFolders.length === 0) {
      unprocessedFolders = folders.filter((f) => !f.archived && !f.processed);
    }

    // If there are no unprocessed folders at all, do nothing
    if (unprocessedFolders.length === 0) {
      toast.error("All selected folders have already been processed", {
        richColors: true,
      });
      return;
    }

    // Process the first unprocessed folder
    const folder = unprocessedFolders[0];
    setIsGeneratingEmbeddings(true);

    fetch("http://localhost:7777/dir/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ folderPath: folder.path }),
    })
      .then((response) => response.json())
      .then((data) => {
        const processedFolderPath = data.folderPath;
        setFolders((prevFolders) =>
          prevFolders.map((f) =>
            f.path === processedFolderPath
              ? {
                  path: f.path,
                  selected: f.selected,
                  processed: true,
                  archived: f.archived,
                  name: f.name,
                }
              : f
          )
        );
        setIsGeneratingEmbeddings(false);
      })
      .catch((err) => {
        console.error("Error processing folder:", err);
        toast.error("Failed to process folder", { richColors: true });
        setIsGeneratingEmbeddings(false);
      });
  };

  const value: AppContextType = {
    folders,
    setFolders,
    query,
    setQuery,
    results,
    setResults,
    sidebarOpen,
    setSidebarOpen,
    loading,
    setLoading,
    selectedFile,
    setSelectedFile,
    embeddingsGenerated,
    setEmbeddingsGenerated,
    embeddingResults,
    setEmbeddingResults,
    isGeneratingEmbeddings,
    setIsGeneratingEmbeddings,
    isSearchDisabled,
    hasUnprocessedSelectedFolders,
    handleSelectFolder,
    toggleFolderSelection,
    archiveFolder,
    unarchiveFolder,
    permanentlyDeleteFolder,
    handleSearch,
    handleFileClick,
    handleCloseFile,
    preprocess,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
