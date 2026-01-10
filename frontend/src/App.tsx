import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { Search, Plus, ChevronRight, ChevronLeft, Folder } from "lucide-react"

function App() {
  const [selectedFolders, setSelectedFolders] = useState<string[]>([])
  const [query, setQuery] = useState("")
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSelectFolder = async () => {
    const result = await window.electronAPI.openDirectory()
    if (!result.canceled) {
      const folderPath = result.filePaths[0]
      const files = await window.electronAPI.readDirectory(folderPath)
      console.log(files)
      setSelectedFolders((prev) => [...prev, folderPath])

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

  const getQueryResults = async () => {
    const params = new URLSearchParams({
      q: query,
    })

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
      const data = await getQueryResults()
      setResults(data)
    } catch (err: any) {
      setError(err.message ?? "Search failed")
    } finally {
      setLoading(false)
    }
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
          className={`border-r bg-white transition-all duration-300 ${
            sidebarOpen ? "w-64" : "w-12"
          }`}
        >
          <div className="flex h-full flex-col">
            {/* Sidebar Toggle */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="flex items-center justify-center border-b p-3 hover:bg-zinc-50"
            >
              {sidebarOpen ? (
                <ChevronLeft className="h-5 w-5 text-zinc-600" />
              ) : (
                <ChevronRight className="h-5 w-5 text-zinc-600" />
              )}
            </button>

            {/* Sidebar Content */}
            {sidebarOpen && (
              <div className="flex-1 overflow-y-auto p-4">
                <h2 className="mb-4 text-sm font-semibold text-zinc-700">Folders</h2>
                <div className="space-y-2">
                  {selectedFolders.length === 0 ? (
                    <p className="text-sm text-zinc-500">No folders added yet</p>
                  ) : (
                    selectedFolders.map((folder, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 rounded-lg border bg-white p-3 text-sm hover:bg-zinc-50"
                      >
                        <Folder className="h-4 w-4 text-zinc-500" />
                        <span className="truncate text-zinc-700">{folder.split('/').pop()}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex flex-1 flex-col items-center justify-center p-8">
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
              <p className="mt-4 text-sm text-zinc-500">
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

          {results && (
            <div className="w-full max-w-4xl">
              <h2 className="mb-4 text-xl font-semibold text-zinc-800">Search Results</h2>
              <div className="space-y-3">
                {results.results && results.results.length > 0 ? (
                  results.results.map((result: any, index: number) => (
                    <div
                      key={index}
                      className="rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
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
                    </div>
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
