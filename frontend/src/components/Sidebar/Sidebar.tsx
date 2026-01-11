import { Button } from "@/components/ui/button"
import { ChevronRight, ChevronLeft, Plus } from "lucide-react"
import { useApp } from "@/context/AppContext"
import { FolderItem } from "@/components/FolderItem/FolderItem"

export function Sidebar() {
  const {
    folders,
    sidebarOpen,
    setSidebarOpen,
    handleSelectFolder,
    toggleFolderSelection,
    removeFolder,
  } = useApp()

  return (
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
                    <FolderItem
                      key={index}
                      folder={folder}
                      index={index}
                      onToggle={toggleFolderSelection}
                      onRemove={removeFolder}
                    />
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
  )
}
