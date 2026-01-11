import { useApp } from "@/context/AppContext";
import { EmbeddingResults } from "@/components/EmbeddingResults/EmbeddingResults";

export function EmptyState() {
  const { embeddingResults } = useApp();

  return (
    <div className="text-center">
      <h2 className="text-2xl font-semibold text-zinc-800">
        Welcome, start by adding some folders!
      </h2>
      <p className="mt-4 text-center text-sm text-zinc-500">
        Add and upload folders in the sidebar to begin searcing through your
        documents.
      </p>
      <EmbeddingResults embeddingResults={embeddingResults} />
    </div>
  );
}
