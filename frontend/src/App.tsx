import { AppProvider } from "@/context/AppContext"
import { SearchBar } from "@/components/SearchBar/SearchBar"
import { Sidebar } from "@/components/Sidebar/Sidebar"
import { MainContent } from "@/components/MainContent/MainContent"

function AppContent() {
  return (
    <div className="flex h-screen flex-col bg-zinc-50">
      {/* Top Search Bar */}
      <SearchBar />

      {/* Main Layout with Sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <MainContent />
      </div>
    </div>
  )
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  )
}

export default App
