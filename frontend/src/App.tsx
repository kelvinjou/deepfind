import { AppProvider } from "@/context/AppContext";
import { SearchBar } from "@/components/SearchBar/SearchBar";
import { Sidebar } from "@/components/Sidebar/Sidebar";
import { MainContent } from "@/components/MainContent/MainContent";
import { Toaster } from "sonner";

function AppContent() {
  return (
    <div className="flex h-screen bg-zinc-50">
      {/* Sidebar on the left, full height */}
      <Sidebar />

      {/* Right side with column layout */}
      <div className="flex flex-1 flex-col">
        {/* Main content takes most space */}
        <MainContent />

        {/* Search bar at bottom */}
        <SearchBar />
      </div>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
      <Toaster position="top-center" closeButton={true} />
    </AppProvider>
  );
}

export default App;
