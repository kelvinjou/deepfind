import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"

function App() {
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null)
  const [query, setQuery] = useState("");

  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectFolder = async () => {
    const result = await window.electronAPI.openDirectory()
    if (!result.canceled) {
      const folderPath = result.filePaths[0]
      const files = await window.electronAPI.readDirectory(folderPath)
      console.log(files)
      setSelectedFolder(folderPath)
    }
  }

  const handleSubmit = async () => {
    const newSubmission = {
      "folderPath": selectedFolder
    }

    try {
      const response = await fetch("http://localhost:7777/dir/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newSubmission)
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

  const getQueryResults = async () => {
    const params = new URLSearchParams({
      q: query,
    });

    const response = await fetch(`http://localhost:7777/query/?${params.toString()}`,
      {
        method: "GET",
      }
    );
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getQueryResults();
      setResults(data);
    } catch (err: any) {
      setError(err.message ?? "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-svh flex-col items-center justify-center px-4 py-6 gap-4">
      <Button onClick={handleSelectFolder}>Select a Folder</Button>
      {selectedFolder && <p>Selected: {selectedFolder}</p>}

      <Button onClick={handleSubmit}>Process</Button>

      <div className="flex w-full max-w-2xl items-center gap-3">
        <Input placeholder="Query" onChange={(e) => setQuery(e.target.value)} />
        <div style={{ flex: 1}} />
        <Button onClick={handleSearch} disabled={loading}>{loading ? "Searching..." : "Search"}</Button>
      </div>
    </div>
  )
}

export default App
