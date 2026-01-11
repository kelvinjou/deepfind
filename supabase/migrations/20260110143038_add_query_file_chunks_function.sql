-- Drop the old function if it exists
DROP FUNCTION IF EXISTS query_file_chunks(vector, float, int, text[]);

-- Clean rewrite: semantic search function using pure SQL
CREATE FUNCTION query_file_chunks (
  query_embedding vector(768),
  match_threshold float DEFAULT 0.1,
  match_count int DEFAULT 10,
  archived_folders text[] DEFAULT array[]::text[]
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
LANGUAGE sql
STABLE
AS $$
  SELECT
    c.id,
    c.file_id,
    c.chunk_index,
    c.content,
    c.chunk_metadata,
    f.file_name,
    f.file_path,
    f.mime_type,
    (1 - (c.embedding <=> query_embedding))::float
  FROM chunks c
  INNER JOIN files f ON c.file_id = f.id
  WHERE c.embedding IS NOT NULL
    AND (1 - (c.embedding <=> query_embedding)) > match_threshold
    AND (
      archived_folders = array[]::text[]
      OR NOT EXISTS (
        SELECT 1
        FROM unnest(archived_folders) AS archived_path
        WHERE f.file_path LIKE archived_path || '%'
      )
    )
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
$$;
