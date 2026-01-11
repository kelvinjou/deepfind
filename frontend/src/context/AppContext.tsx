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
  matchCount: number;
  setMatchCount: React.Dispatch<React.SetStateAction<number>>;

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
  archiveFolder: (folder: FolderData) => void;
  unarchiveFolder: (folder: FolderData) => void;
  permanentlyDeleteFolder: (folder: FolderData) => Promise<void>;
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
  const [matchCount, setMatchCount] = useState(10);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);
  const [embeddingsGenerated, setEmbeddingsGenerated] = useState(false);
  const [embeddingResults, setEmbeddingResults] = useState<EmbeddingResult[]>(
    []
  );
  const [isGeneratingEmbeddings, setIsGeneratingEmbeddings] = useState(false);

  const isSearchDisabled = folders.length === 0;

  const hasUnprocessedSelectedFolders = folders.some(
    (f) => !f.archived && !f.processed
  );

  const handleSelectFolder = async () => {
    const result = await window.electronAPI.openDirectory();
    if (!result.canceled) {
      const newFolders = result.filePaths.filter((folderPath) => {
        // Skip if folder already added
        return !folders.some((folder) => folder.path === folderPath);
      });

      if (newFolders.length === 0) {
        toast.error("All selected folders have already been added", {
          richColors: true,
        });
        return;
      }

      // Validate all folders can be read
      for (const folderPath of newFolders) {
        try {
          await window.electronAPI.readDirectory(folderPath);
        } catch (err) {
          console.error(`Failed to read folder: ${folderPath}`, err);
          toast.error(`Failed to read folder: ${folderPath}`, {
            richColors: true,
          });
          return;
        }
      }

      // Add all valid folders to state
      const foldersToAdd = newFolders.map((folderPath) => ({
        path: folderPath,
        selected: true,
        processed: false,
        archived: false,
        name: folderPath.split("/").pop() || folderPath,
      }));

      setFolders((prev) => [...prev, ...foldersToAdd]);

      toast.success(
        `${newFolders.length} folder${
          newFolders.length !== 1 ? "s" : ""
        } added`,
        { richColors: true }
      );
    }
  };

  const archiveFolder = (folder: FolderData) => {
    setFolders((prev) => {
      // If folder hasn't been processed, remove it completely (no DB data to archive)
      if (!folder.processed) {
        return prev.filter((f) => f.path !== folder.path);
      }

      // Otherwise, archive it (marks it to be excluded from queries)
      return prev.map((f) =>
        f.path === folder.path ? { ...f, archived: true } : f
      );
    });

    toast.info(`Folder "${folder.name}" archived`, { richColors: true });

    // Reset query state since results may now be invalid
    setResults(null);
    setSelectedFile(null);
  };

  const unarchiveFolder = (folder: FolderData) => {
    setFolders((prev) =>
      prev.map((f) => (f.path === folder.path ? { ...f, archived: false } : f))
    );

    toast.success(`Folder "${folder.name}" unarchived`, { richColors: true });

    // Reset query state since results may now be invalid
    setResults(null);
    setSelectedFile(null);
  };

  const permanentlyDeleteFolder = async (folder: FolderData) => {
    const folderPath = folder.path;
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

      toast.success(
        `Folder "${folder.name}" permanently deleted. Deleted ${data.deletedCount} files.`,
        { richColors: true }
      );

      // Remove folder from state after successful deletion
      setFolders((prev) => prev.filter((f) => f.path !== folderPath));

      // Reset query state since results may now be invalid
      setResults(null);
      setSelectedFile(null);
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
      .filter((folder) => !folder.archived && folder.processed)
      .map((folder) => folder.path);

    const archivedFolderPaths = folders
      .filter((folder) => folder.archived)
      .map((folder) => folder.path);

    const params = new URLSearchParams({
      query_text: query,
      match_count: matchCount.toString()
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
    console.log(response);
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
    // Get all unprocessed folders (excluding archived)
    const unprocessedFolders = folders.filter(
      (f) => !f.archived && !f.processed
    );

    // If there are no unprocessed folders, do nothing
    if (unprocessedFolders.length === 0) {
      toast.error("All selected folders have already been processed", {
        richColors: true,
      });
      return;
    }

    setIsGeneratingEmbeddings(true);
    const folderPaths = unprocessedFolders.map((f) => f.path);

    fetch("http://localhost:7777/dir/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ folderPath: folderPaths }),
    })
      .then((response) => response.json())
      .then((data) => {
        // Mark all processed folders
        const processedPaths = new Set(data.folderPaths);
        setFolders((prevFolders) =>
          prevFolders.map((f) =>
            processedPaths.has(f.path)
              ? {
                  path: f.path,
                  processed: true,
                  archived: f.archived,
                  name: f.name,
                }
              : f
          )
        );
        setIsGeneratingEmbeddings(false);
        toast.success(
          `Finished processing ${unprocessedFolders.length} folder${
            unprocessedFolders.length !== 1 ? "s" : ""
          }`,
          { richColors: true }
        );
      })
      .catch((err) => {
        console.error("Error processing folders:", err);
        toast.error("Failed to process folders", { richColors: true });
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
    matchCount,
    setMatchCount,
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
