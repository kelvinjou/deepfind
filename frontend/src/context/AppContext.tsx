import { createContext, useContext, useState, ReactNode } from "react";
import {
  FolderData,
  SelectedFile,
  SearchResults,
  EmbeddingResult,
} from "@/types/app";

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
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;

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

  // Actions
  handleSelectFolder: () => Promise<void>;
  toggleFolderSelection: (index: number) => void;
  removeFolder: (index: number) => void;
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
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);
  const [embeddingsGenerated, setEmbeddingsGenerated] = useState(false);
  const [embeddingResults, setEmbeddingResults] = useState<EmbeddingResult[]>(
    []
  );
  const [isGeneratingEmbeddings, setIsGeneratingEmbeddings] = useState(false);

  const isSearchDisabled =
    folders.length === 0 || folders.some((f) => f.selected && !f.processed);

  const handleSelectFolder = async () => {
    const result = await window.electronAPI.openDirectory();
    if (!result.canceled) {
      const folderPath = result.filePaths[0];

      if (folders.some((folder) => folder.path === folderPath)) {
        setError("Folder already added");
        setTimeout(() => setError(null), 2000);
        return;
      }

      await window.electronAPI.readDirectory(folderPath);
      setFolders((prev) => [
        ...prev,
        { path: folderPath, selected: true, processed: false },
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

  const removeFolder = (index: number) => {
    setFolders((prev) => prev.filter((_, i) => i !== index));
  };

  const getQueryResults = async () => {
    const selectedFolderPaths = folders
      .filter((folder) => folder.selected && folder.processed)
      .map((folder) => folder.path);

    const params = new URLSearchParams({
      query_text: query,
    });

    if (selectedFolderPaths.length > 0) {
      params.append("folders", JSON.stringify(selectedFolderPaths));
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
    setError(null);

    try {
      const data = await getQueryResults();
      setResults(data);
    } catch (err: unknown) {
      console.error("Search error:", err);
      const errorMessage = err instanceof Error ? err.message : "Search failed";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = async (filePath: string, fileName: string) => {
    if (!fileName.endsWith(".txt")) {
      setError("Only .txt files can be previewed");
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      const content = await window.electronAPI.readFile(filePath);
      setSelectedFile({
        path: filePath,
        content: content,
        name: fileName,
      });
      setError(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(`Failed to read file: ${errorMessage}`);
    }
  };

  const handleCloseFile = () => {
    setSelectedFile(null);
  };

  const getSelectedFolders = () => {
    return folders.filter((folder) => folder.selected);
  };

  const preprocess = async () => {
    let selectedFolders = getSelectedFolders();
    if (selectedFolders.length === 0) selectedFolders = folders;
    const folder = selectedFolders[0];

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
        setFolders(
          folders.map((f) =>
            f.path === processedFolderPath
              ? { path: f.path, selected: f.selected, processed: true }
              : f
          )
        );
      })
      .catch((err) => {
        console.log(err);
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
    error,
    setError,
    selectedFile,
    setSelectedFile,
    embeddingsGenerated,
    setEmbeddingsGenerated,
    embeddingResults,
    setEmbeddingResults,
    isGeneratingEmbeddings,
    setIsGeneratingEmbeddings,
    isSearchDisabled,
    handleSelectFolder,
    toggleFolderSelection,
    removeFolder,
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
