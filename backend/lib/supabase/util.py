# Supabase database utility functions for inserting and querying files/chunks.

import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """Client for interacting with the Supabase database for file and chunk operations."""

    _instance: "SupabaseClient | None" = None

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SECRET_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SECRET_KEY must be set in .env")
        self._client: Client = create_client(url, key)

    @classmethod
    def get_instance(cls) -> "SupabaseClient":
        """Get singleton instance of the client."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------

    def get_file(
        self,
        *,
        file_id: str | None = None,
        file_hash: str | None = None,
        file_path: str | None = None,
    ) -> dict | None:
        """
        Get a file record by ID, hash, or path.

        Args:
            file_id: UUID of the file
            file_hash: SHA256 hash of the file
            file_path: Path to the file

        Returns:
            File record dict or None if not found
        """
        query = self._client.table("files").select("*")

        if file_id:
            query = query.eq("id", file_id)
        elif file_hash:
            query = query.eq("file_hash", file_hash)
        elif file_path:
            query = query.eq("file_path", file_path)
        else:
            raise ValueError("Must provide file_id, file_hash, or file_path")

        result = query.execute()
        return result.data[0] if result.data else None

    def get_all_files(self) -> list[dict]:
        """
        Get all file records from the database.

        Returns:
            List of file record dicts
        """
        result = self._client.table("files").select("*").execute()
        return result.data

    def file_exists(
        self,
        *,
        file_id: str | None = None,
        file_hash: str | None = None,
        file_path: str | None = None,
    ) -> bool:
        """
        Check if a file exists by ID, hash, or path.

        Args:
            file_id: UUID of the file
            file_hash: SHA256 hash of the file
            file_path: Path to the file

        Returns:
            True if file exists, False otherwise
        """
        return self.get_file(file_id=file_id, file_hash=file_hash, file_path=file_path) is not None

    def insert_file(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        mime_type: str,
        file_hash: str,
        last_modified_at: datetime,
        file_size: int | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Insert a file record into the database.

        Args:
            file_path: Full path to the file
            file_name: Name of the file
            file_type: Type/extension of the file (e.g., "audio", "pdf", "text")
            mime_type: MIME type of the file
            file_hash: SHA256 hash of the file
            last_modified_at: When the file was last modified
            file_size: Size of the file in bytes
            metadata: Additional metadata as dict (stored as JSONB)

        Returns:
            The UUID of the inserted file record
        """
        data = {
            "file_path": file_path,
            "file_name": file_name,
            "file_type": file_type,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "file_size": file_size,
            "last_modified_at": last_modified_at.isoformat(),
            "processing_status": "processing",
            "metadata": metadata or {},
        }

        result = self._client.table("files").insert(data).execute()
        return result.data[0]["id"]

    def update_file_status(
        self,
        file_id: str,
        status: str,
        processed_at: datetime | None = None,
    ) -> None:
        """
        Update the processing status of a file.

        Args:
            file_id: UUID of the file
            status: New status ('pending', 'processing', 'completed', 'failed')
            processed_at: When processing completed (optional)
        """
        data = {"processing_status": status}
        if processed_at:
            data["processed_at"] = processed_at.isoformat()

        self._client.table("files").update(data).eq("id", file_id).execute()

    def delete_file(
        self,
        *,
        file_id: str | None = None,
        file_hash: str | None = None,
        file_path: str | None = None,
    ) -> bool:
        """
        Delete a file and all its associated chunks by ID, hash, or path.

        Chunks are automatically deleted due to CASCADE on foreign key.

        Args:
            file_id: UUID of the file to delete
            file_hash: SHA256 hash of the file to delete
            file_path: Path of the file to delete

        Returns:
            True if file was deleted, False if not found
        """
        query = self._client.table("files").delete()

        if file_id:
            query = query.eq("id", file_id)
        elif file_hash:
            query = query.eq("file_hash", file_hash)
        elif file_path:
            query = query.eq("file_path", file_path)
        else:
            raise ValueError("Must provide file_id, file_hash, or file_path")

        result = query.execute()
        return len(result.data) > 0

    def delete_all_files(self) -> int:
        """
        Delete all files and chunks from the database.

        Use this to reset a study session or clear all data.

        Returns:
            Number of files deleted
        """
        result = (
            self._client.table("files")
            .delete()
            .neq("id", "00000000-0000-0000-0000-000000000000")
            .execute()
        )
        return len(result.data)

    # -------------------------------------------------------------------------
    # Chunk Operations
    # -------------------------------------------------------------------------

    def insert_chunks(
        self,
        file_id: str,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> int:
        """
        Batch insert chunks with embeddings for a file.

        Args:
            file_id: UUID of the parent file
            chunks: List of chunk dicts with 'content', 'chunk_index', 'chunk_metadata'
            embeddings: List of embedding vectors (must match length of chunks)

        Returns:
            Number of chunks inserted
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")

        rows = [
            {
                "file_id": file_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "embedding": embedding,
                "chunk_metadata": chunk["chunk_metadata"],
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        result = self._client.table("chunks").insert(rows).execute()
        return len(result.data)

    def get_chunks(self, file_id: str) -> list[dict]:
        """
        Get all chunks for a file.

        Args:
            file_id: UUID of the parent file

        Returns:
            List of chunk records ordered by chunk_index
        """
        result = (
            self._client.table("chunks")
            .select("*")
            .eq("file_id", file_id)
            .order("chunk_index")
            .execute()
        )
        return result.data

    # -------------------------------------------------------------------------
    # High-Level Operations
    # -------------------------------------------------------------------------

    def process_file(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        mime_type: str,
        file_hash: str,
        last_modified_at: datetime,
        chunks: list[dict],
        embeddings: list[list[float]],
        file_size: int | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        High-level function to insert a file and its chunks in one operation.

        Checks if file already exists (by hash), inserts file record,
        inserts all chunks with embeddings, and updates status to completed.

        Args:
            file_path: Full path to the file
            file_name: Name of the file
            file_type: Type of file (e.g., "audio", "pdf")
            mime_type: MIME type
            file_hash: SHA256 hash
            last_modified_at: File modification time
            chunks: List of chunk dicts
            embeddings: List of embedding vectors
            file_size: Size in bytes
            metadata: Additional metadata

        Returns:
            The UUID of the file record

        Raises:
            ValueError: If file already exists
        """
        if self.file_exists(file_hash=file_hash):
            raise ValueError(f"File with hash {file_hash} already exists")

        file_id = self.insert_file(
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_hash=file_hash,
            last_modified_at=last_modified_at,
            file_size=file_size,
            metadata=metadata,
        )

        self.insert_chunks(file_id, chunks, embeddings)
        self.update_file_status(file_id, "completed", datetime.now())

        return file_id


# Convenience function to get the singleton instance
def get_supabase_client() -> SupabaseClient:
    """Get the singleton SupabaseClient instance."""
    return SupabaseClient.get_instance()


if __name__ == "__main__":
    print("Testing Supabase connection...")
    client = get_supabase_client()
    files = client.get_all_files()
    print(f"Connection successful! Files in DB: {len(files)}")
