-- Migration: Change embedding dimension from 512 to 768
-- This requires clearing existing data since dimensions must match

-- Drop the existing index
DROP INDEX IF EXISTS chunks_embedding_idx;

-- Clear existing chunks (embeddings have wrong dimension)
DELETE FROM chunks;

-- Clear existing files
DELETE FROM files;

-- Alter the embedding column to use 768 dimensions
ALTER TABLE chunks
  ALTER COLUMN embedding TYPE vector(768);

-- Recreate the index for the new dimension
CREATE INDEX chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops);

-- Update the query function to use 768 dimensions
CREATE OR REPLACE FUNCTION query_file_chunks (
  query_embedding vector(768),
  match_threshold float default 0.5,
  match_count int default 10
)
RETURNS TABLE (
  chunk_id uuid,
  file_id uuid,
  chunk_index int,
  content text,
  chunk_metadata jsonb,
  file_name text,
  file_path text,
  mime_type text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    c.id AS chunk_id,
    c.file_id,
    c.chunk_index,
    c.content,
    c.chunk_metadata,
    f.file_name,
    f.file_path,
    f.mime_type,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM chunks c
  JOIN files f ON c.file_id = f.id
  WHERE c.embedding IS NOT NULL
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding ASC
  LIMIT match_count;
$$;
