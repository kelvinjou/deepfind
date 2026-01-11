-- Function to perform semantic search on chunks using vector similarity
create or replace function query_file_chunks (
  query_embedding public.vector(512),
  match_threshold float default 0.5,
  match_count int default 10
)
returns table (
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
language sql stable
as $$
  select
    c.id as chunk_id,
    c.file_id,
    c.chunk_index,
    c.content,
    c.chunk_metadata,
    f.file_name,
    f.file_path,
    f.mime_type,
    1 - (c.embedding <=> query_embedding) as similarity
  from chunks c
  join files f on c.file_id = f.id
  where c.embedding is not null
    and 1 - (c.embedding <=> query_embedding) > match_threshold
  order by c.embedding <=> query_embedding asc
  limit match_count;
$$;
