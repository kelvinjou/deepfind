import { Button } from "@/components/ui/button";
import { ChevronRight, ChevronLeft, Plus, Upload } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { FolderItem } from "@/components/FolderItem/FolderItem";
import { ArchivedFolderItem } from "@/components/ArchivedFolderItem/ArchivedFolderItem";

export function Sidebar() {
  const {
    folders,
    sidebarOpen,
    setSidebarOpen,
    handleSelectFolder,
    toggleFolderSelection,
    archiveFolder,
    unarchiveFolder,
    permanentlyDeleteFolder,
    preprocess,
    hasUnprocessedSelectedFolders,
    isGeneratingEmbeddings,
  } = useApp();

  const activeFolders = folders.filter((f) => !f.archived);
  const archivedFolders = folders.filter((f) => f.archived);

  return (
    <div
      className={`relative h-full border-r bg-white transition-all duration-300 ${
        sidebarOpen ? "w-64" : "w-12"
      }`}
    >
      <div className="flex h-full flex-col">
        {/* Sidebar Toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute right-0 top-0 flex items-center justify-center bg-white hover:bg-zinc-50 z-10 p-3"
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
            <div className="flex-1 overflow-y-auto p-4 mt-1">
              {/* Active Folders */}
              <h2 className="mb-2 text-sm font-semibold text-zinc-700">
                Folders
              </h2>
              <div className="flex flex-col gap-1 mb-4">
                {activeFolders.length === 0 ? (
                  <p className="text-sm text-zinc-500">No folders added yet</p>
                ) : (
                  activeFolders.map((folder, index) => (
                    <FolderItem
                      key={index}
                      folder={folder}
                      index={folders.indexOf(folder)}
                      onToggle={toggleFolderSelection}
                      onRemove={archiveFolder}
                    />
                  ))
                )}
              </div>

              {/* Archived Folders */}
              {archivedFolders.length > 0 && (
                <>
                  <h2 className="mb-2 text-sm font-semibold text-zinc-700 mt-4">
                    Archived
                  </h2>
                  <div className="flex flex-col gap-1">
                    {archivedFolders.map((folder, index) => (
                      <ArchivedFolderItem
                        key={index}
                        folder={folder}
                        index={folders.indexOf(folder)}
                        onUnarchive={unarchiveFolder}
                        onDelete={permanentlyDeleteFolder}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
            <div className="flex flex-col gap-2 border-t p-4">
              <Button
                onClick={preprocess}
                disabled={
                  !hasUnprocessedSelectedFolders || isGeneratingEmbeddings
                }
                className="w-full flex items-center justify-center gap-2"
                variant={
                  !hasUnprocessedSelectedFolders || isGeneratingEmbeddings
                    ? "outline"
                    : "default"
                }
              >
                <Upload className="h-4 w-4" />
                {isGeneratingEmbeddings ? "Processing..." : "Process Folders"}
              </Button>
              <Button
                onClick={handleSelectFolder}
                disabled={isGeneratingEmbeddings}
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
  );
}
