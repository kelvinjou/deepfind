-- Function to perform semantic search on chunks using vector similarity
CREATE OR REPLACE FUNCTION query_file_chunks (
  query_embedding vector(768),
  match_threshold float default 0.5,
  match_count int default 10,
  archived_folders text[] default '{}'
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
    -- Exclude files from archived folders
    AND NOT EXISTS (
      SELECT 1
      FROM unnest(archived_folders) AS af(folder)
      WHERE f.file_path LIKE af.folder || '%'
    )
  ORDER BY c.embedding <=> query_embedding ASC
  LIMIT match_count;
$$;
