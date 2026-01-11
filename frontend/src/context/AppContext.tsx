import {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
  useRef,
} from "react";
import {
  FolderData,
  SelectedFile,
  SearchResults,
  EmbeddingResult,
} from "@/types/app";
import { toast } from "sonner";

interface AgentMetadata {
  topic?: string;
  documentsFound?: number;
  fileType?: string;
}

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

  // Agent state
  agentOutput: string;
  setAgentOutput: React.Dispatch<React.SetStateAction<string>>;
  agentMetadata: AgentMetadata | null;
  setAgentMetadata: React.Dispatch<React.SetStateAction<AgentMetadata | null>>;
  isAgentRunning: boolean;
  setIsAgentRunning: React.Dispatch<React.SetStateAction<boolean>>;
  showOutputPanel: boolean;
  setShowOutputPanel: React.Dispatch<React.SetStateAction<boolean>>;

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
  closeOutputPanel: () => void;
  summarizeFile: (fileName: string, filePath: string, content?: string) => Promise<void>;
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

  // Agent state
  const [agentOutput, setAgentOutput] = useState("");
  const [agentMetadata, setAgentMetadata] = useState<AgentMetadata | null>(null);
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const [showOutputPanel, setShowOutputPanel] = useState(false);
  const agentAbortControllerRef = useRef<AbortController | null>(null);

  // Fetch initial folders from backend on mount
  useEffect(() => {
    const fetchInitialFolders = async () => {
      try {
        const response = await fetch("http://localhost:7777/folders/");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Transform API response to FolderData format
        const initialFolders: FolderData[] = data.folders.map(
          (folder: {
            name: string;
            path: string;
            files: Array<{ file_name: string }>;
          }) => ({
            path: folder.path,
            name: folder.name,
            processed: true,
            archived: false,
            files: folder.files.map((f) => f.file_name),
          })
        );

        setFolders(initialFolders);
      } catch (err) {
        console.error("Failed to fetch initial folders:", err);
        // Don't show error toast on initial load - it's fine if backend isn't ready yet
      }
    };

    fetchInitialFolders();
  }, []);

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
        toast.error("All selected folder(s) have already been added", {
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
        files: [],
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
    const archivedFolderPaths = folders
      .filter((folder) => folder.archived)
      .map((folder) => folder.path);

    const params = new URLSearchParams({
      query_text: query,
      match_count: matchCount.toString(),
    });

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

  // Detect if the query is asking for summarization
  const detectSummarizeIntent = (queryText: string): boolean => {
    const summarizeKeywords = ["summarize", "summary", "synthesize", "what do the documents say"];
    const lowerQuery = queryText.toLowerCase();
    return summarizeKeywords.some(keyword => lowerQuery.includes(keyword));
  };

  // Run agent task with SSE streaming
  const runAgentTask = async (prompt: string) => {
    // Cancel any existing request
    if (agentAbortControllerRef.current) {
      agentAbortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const abortController = new AbortController();
    agentAbortControllerRef.current = abortController;

    setIsAgentRunning(true);
    setAgentOutput("");
    setAgentMetadata(null);
    setShowOutputPanel(true);
    setSelectedFile(null);
    setResults(null);

    try {
      const response = await fetch("http://localhost:7777/agent/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt, match_count: matchCount }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Check if this is a streaming response
      const contentType = response.headers.get("content-type");
      if (contentType?.includes("text/event-stream")) {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        let streamDone = false;
        while (!streamDone) {
          const { done, value } = await reader.read();
          if (done) {
            streamDone = true;
            continue;
          }

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.metadata) {
                  setAgentMetadata(data.metadata);
                } else if (data.content) {
                  setAgentOutput(prev => prev + data.content);
                } else if (data.done) {
                  // Stream complete
                }
              } catch {
                // Skip malformed JSON
              }
            }
          }
        }
      } else {
        // Non-streaming response (not an agent task)
        const data = await response.json();
        if (data.status === "not_agent_task") {
          // Fall back to regular search
          setShowOutputPanel(false);
          const searchData = await getQueryResults();
          setResults(searchData);
        }
      }
    } catch (err: unknown) {
      // Don't show error if request was aborted (user cancelled)
      if (err instanceof Error && err.name === "AbortError") {
        console.log("Agent request cancelled");
        return;
      }
      console.error("Agent error:", err);
      const errorMessage = err instanceof Error ? err.message : "Agent task failed";
      toast.error(errorMessage, { richColors: true });
    } finally {
      setIsAgentRunning(false);
      agentAbortControllerRef.current = null;
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    setSelectedFile(null);

    // Check if this is a summarize request
    if (detectSummarizeIntent(query)) {
      setLoading(false);
      await runAgentTask(query);
      return;
    }

    // Regular search
    setShowOutputPanel(false);
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

  const closeOutputPanel = () => {
    // Abort any ongoing agent request
    if (agentAbortControllerRef.current) {
      agentAbortControllerRef.current.abort();
      agentAbortControllerRef.current = null;
    }
    setShowOutputPanel(false);
    setAgentOutput("");
    setAgentMetadata(null);
    setIsAgentRunning(false);
  };

  // Summarize a single file's content
  const summarizeFile = async (fileName: string, filePath: string, content?: string) => {
    // Cancel any existing request
    if (agentAbortControllerRef.current) {
      agentAbortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const abortController = new AbortController();
    agentAbortControllerRef.current = abortController;

    setIsAgentRunning(true);
    setAgentOutput("");
    setAgentMetadata(null);
    setShowOutputPanel(true);
    setSelectedFile(null);

    try {
      const response = await fetch("http://localhost:7777/summarize-file/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fileName, filePath, content }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      let streamDone = false;
      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) {
          streamDone = true;
          continue;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.metadata) {
                setAgentMetadata({
                  topic: `Summary of ${data.metadata.fileName}`,
                  fileType: data.metadata.fileType
                });
              } else if (data.content) {
                setAgentOutput(prev => prev + data.content);
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }
    } catch (err: unknown) {
      // Don't show error if request was aborted (user cancelled)
      if (err instanceof Error && err.name === "AbortError") {
        console.log("Summarize request cancelled");
        return;
      }
      console.error("Summarize error:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to summarize file";
      toast.error(errorMessage, { richColors: true });
    } finally {
      setIsAgentRunning(false);
      agentAbortControllerRef.current = null;
    }
  };

  const handleFileClick = async (filePath: string, fileName: string) => {
    // if (!fileName.endsWith(".txt")) {
    //   toast.error("Only .txt files can be previewed", { richColors: true });
    //   return;
    // }

    try {
      const content = await window.electronAPI.readFile(filePath);
      console.log(fileName);
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
        // Mark all processed folders and fetch updated folder data
        const processedPaths = new Set(data.folderPaths);
        setFolders((prevFolders) =>
          prevFolders.map((f) =>
            processedPaths.has(f.path)
              ? {
                  path: f.path,
                  processed: true,
                  archived: f.archived,
                  name: f.name,
                  files: f.files,
                }
              : f
          )
        );

        // Fetch updated folder data with files from the database
        return fetch("http://localhost:7777/folders/").then((res) =>
          res.json()
        );
      })
      .then((data) => {
        // Merge updated folder data with existing state, preserving archived status
        const updatedFoldersMap: Map<
          string,
          { path: string; name: string; files: string[] }
        > = new Map(
          data.folders.map(
            (folder: {
              path: string;
              name: string;
              files: Array<{ file_name: string }>;
            }) => [
              folder.path,
              {
                path: folder.path,
                name: folder.name,
                files: folder.files.map(
                  (f: { file_name: string }) => f.file_name
                ),
              },
            ]
          )
        );

        setFolders((prevFolders) =>
          prevFolders.map((f) => {
            const updated = updatedFoldersMap.get(f.path);
            return updated
              ? {
                  path: f.path,
                  processed: true,
                  archived: f.archived,
                  name: updated.name,
                  files: updated.files,
                }
              : f;
          })
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
    agentOutput,
    setAgentOutput,
    agentMetadata,
    setAgentMetadata,
    isAgentRunning,
    setIsAgentRunning,
    showOutputPanel,
    setShowOutputPanel,
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
    closeOutputPanel,
    summarizeFile,
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
