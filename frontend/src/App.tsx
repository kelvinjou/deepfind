import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { Search, Plus, ChevronRight, ChevronLeft, Folder, Check, X } from "lucide-react"
import { FileInfo } from "./types/electron"

interface FolderData {
  path: string
  selected: boolean
}

function App() {
  const [folders, setFolders] = useState<FolderData[]>([])
  const [query, setQuery] = useState("")
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<{ path: string; content: string; name: string } | null>(null)

  const handleSelectFolder = async () => {
    const result = await window.electronAPI.openDirectory()
    if (!result.canceled) {
      const folderPath = result.filePaths[0]
      const files = await window.electronAPI.readDirectory(folderPath)
      console.log(files)
      setFolders((prev) => [...prev, { path: folderPath, selected: true }])

      // Automatically submit the folder for processing
      try {
        const response = await fetch("http://localhost:7777/dir/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ folderPath })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log("Success:", data)
      } catch (error) {
        console.error("Error:", error)
      }
    }
  }

  const toggleFolderSelection = (index: number) => {
    setFolders((prev) =>
      prev.map((folder, i) =>
        i === index ? { ...folder, selected: !folder.selected } : folder
      )
    )
  }

  const removeFolder = (index: number) => {
    setFolders((prev) => prev.filter((_, i) => i !== index))
  }

  const getQueryResults = async () => {
    const selectedFolderPaths = folders
      .filter((folder) => folder.selected)
      .map((folder) => folder.path)

    const params = new URLSearchParams({
      q: query,
    })

    // Add selected folder paths to the query if any are selected
    if (selectedFolderPaths.length > 0) {
      params.append("folders", JSON.stringify(selectedFolderPaths))
    }

    const response = await fetch(`http://localhost:7777/query/?${params.toString()}`,
      {
        method: "GET",
      }
    )
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  }

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
      // Test: Display files from test_files/text
      const testDir = "/Users/baileysay/projects/file-finder/backend/test_files/image"
      const files = await window.electronAPI.readDirectory(testDir)

      console.log("Files from directory:", files)

      const mockResults = {
        results: files
          .filter((file: FileInfo) => !file.isDirectory)
          .map((file: FileInfo) => ({
            file_name: file.name,
            file_path: `${testDir}/${file.name}`,
            content: "Test content preview...",
            similarity_score: Math.random()
          }))
      }

      console.log("Mock results:", mockResults)
      setResults(mockResults)

      // Original API call (commented out for testing)
      // const data = await getQueryResults()
      // setResults(data)
    } catch (err: any) {
      setError(err.message ?? "Search failed")
    } finally {
      setLoading(false)
    }
  }

  const getSelectedFolders = () => {
    return folders.filter((folder) => folder.selected).map((folder) => folder.path)
  }

  const handleFileClick = async (filePath: string, fileName: string) => {
    // Only handle .txt files for now
    if (!fileName.endsWith('.txt')) {
      setError("Only .txt files can be previewed")
      setTimeout(() => setError(null), 3000)
      return
    }

    try {
      const content = await window.electronAPI.readFile(filePath)

      setSelectedFile({
        path: filePath,
        content: content,
        name: fileName

      })
      setError(null)
    } catch (err: any) {
      setError(`Failed to read file: ${err.message}`)
    }
  }

  const handleCloseFile = () => {
    setSelectedFile(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  return (
    <div className="flex h-screen flex-col bg-zinc-50">
      {/* Top Search Bar */}
      <div className="flex items-center gap-3 border-b bg-white px-6 py-4">
        <Search className="h-5 w-5 text-zinc-400" />
        <Input
          placeholder="Search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 border-0 shadow-none focus-visible:ring-0"
        />
      </div>

      {/* Main Layout with Sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div
          className={`relative border-r bg-white transition-all duration-300 ${
            sidebarOpen ? "w-64" : "w-12"
          }`}
        >
          <div className="flex h-full flex-col">
            {/* Sidebar Toggle */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="absolute right-0 top-0 flex items-center justify-center border-b border-l p-3 bg-white hover:bg-zinc-50 z-10 rounded-bl-lg"
            >
              {sidebarOpen ? (
                <ChevronLeft className="h-5 w-5 text-zinc-600" />
              ) : (
                <ChevronRight className="h-5 w-5 text-zinc-600" />
              )}
            </button>

            {/* Sidebar Content */}
            {sidebarOpen && (
              <>
                <div className="flex-1 overflow-y-auto p-4 pt-16">
                  <h2 className="mb-4 text-sm font-semibold text-zinc-700">Folders</h2>
                  <div className="space-y-2">
                    {folders.length === 0 ? (
                      <p className="text-sm text-zinc-500">No folders added yet</p>
                    ) : (
                      folders.map((folder, index) => (
                        <div
                          key={index}
                          className={`flex w-full items-center gap-2 rounded-lg border p-3 text-sm transition-colors ${
                            folder.selected
                              ? "border-blue-500 bg-blue-50"
                              : "bg-white"
                          }`}
                        >
                          <button
                            onClick={() => toggleFolderSelection(index)}
                            className="flex flex-1 items-center gap-2 hover:opacity-80"
                          >
                            <div
                              className={`flex h-5 w-5 items-center justify-center rounded border ${
                                folder.selected
                                  ? "border-blue-500 bg-blue-500"
                                  : "border-zinc-300 bg-white"
                              }`}
                            >
                              {folder.selected && <Check className="h-3 w-3 text-white" />}
                            </div>
                            <Folder className={`h-4 w-4 ${folder.selected ? "text-blue-600" : "text-zinc-500"}`} />
                            <span className={`truncate ${folder.selected ? "text-blue-900" : "text-zinc-700"}`}>
                              {folder.path.split('/').pop()}
                            </span>
                          </button>
                          <button
                            onClick={() => removeFolder(index)}
                            className="flex items-center justify-center rounded p-1 hover:bg-red-100 transition-colors"
                            title="Remove folder"
                          >
                            <X className="h-4 w-4 text-zinc-400 hover:text-red-600" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                <div className="border-t p-4">
                  <Button
                    onClick={handleSelectFolder}
                    className="w-full flex items-center justify-center gap-2"
                    variant="outline"
                  >
                    <Plus className="h-4 w-4" />
                    Add Folder
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <div className={`flex flex-1 flex-col items-center p-8 overflow-y-auto ${!results && !loading && !error ? 'justify-center' : 'justify-start'}`}>
          {!results && !loading && !error && (
            <div className="text-center">
              <Button
                onClick={handleSelectFolder}
                className="flex items-center gap-2 text-lg"
                size="lg"
              >
                <Plus className="h-5 w-5" />
                Add new folder
              </Button>
              <p className="mt-4 text-center text-sm text-zinc-500">
                Add folders to search through your files
              </p>
            </div>
          )}

          {loading && (
            <div className="text-center">
              <p className="text-lg text-zinc-600">Searching...</p>
            </div>
          )}

          {error && (
            <div className="text-center">
              <p className="text-lg text-red-600">Error: {error}</p>
            </div>
          )}

          {selectedFile ? (
            <div className="w-full max-w-4xl">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-zinc-800">{selectedFile.name}</h2>
                <Button onClick={handleCloseFile} variant="outline" size="sm">
                  <X className="h-4 w-4 mr-2" />
                  Close
                </Button>
              </div>
              <p className="text-sm text-zinc-500 mb-4">{selectedFile.path}</p>
              <div className="rounded-lg border bg-white p-6 shadow-sm">
                <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-800 overflow-auto max-h-[60vh]">
                  {selectedFile.content}
                </pre>
              </div>
            </div>
          ) : results && (
            <div className="w-full max-w-4xl">
              <h2 className="mb-4 text-xl font-semibold text-zinc-800">Search Results</h2>
              <div className="space-y-3 pb-8">
                {results.results && results.results.length > 0 ? (
                  results.results.map((result: any, index: number) => (
                    <button
                      key={index}
                      onClick={() => handleFileClick(result.file_path, result.file_name)}
                      className="w-full rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow text-left"
                    >
                      <div className="flex items-start gap-3">
                        <Folder className="h-5 w-5 text-zinc-500 mt-0.5" />
                        <div className="flex-1">
                          <h3 className="font-medium text-zinc-800">{result.file_name}</h3>
                          <p className="text-sm text-zinc-500 mt-1">{result.file_path}</p>
                          {result.content && (
                            <p className="text-sm text-zinc-600 mt-2">{result.content}</p>
                          )}
                          {result.similarity_score && (
                            <p className="text-xs text-zinc-400 mt-2">
                              Similarity: {(result.similarity_score * 100).toFixed(1)}%
                            </p>
                          )}
                        </div>
                      </div>
                    </button>
                  ))
                ) : (
                  <p className="text-center text-zinc-500">No results found</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
