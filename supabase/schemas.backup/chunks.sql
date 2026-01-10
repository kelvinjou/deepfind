-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Chunks table: processed content with embeddings
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,  -- 0 for images (single chunk), 0+ for multi-chunk content
    content TEXT NOT NULL,  -- extracted/transcribed/summarized text
    embedding VECTOR(512),  -- adjust dimension based on your embedding model
    chunk_metadata JSONB NOT NULL,  -- store chunk-specific info (page number for PDFs, timestamp for audio, etc.)
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(file_id, chunk_index)
);

/*
    chunk_metadata examples for each file type:

    -- Image (single chunk, is_whole_file: true)
    {
        "is_whole_file": true
    }

    -- Audio (chunked by time segments)
    {
        "timestamp_start": "00:02:30",
        "timestamp_end": "00:03:15"
    }

    -- PDF (chunked by pages/sections)
    {
        "page_number": 5,
        "has_embedded_image": false
    }

    -- PDF (chunk from an embedded image)
    {
        "page_number": 8,
        "is_embedded_image": true,
        "image_index": 2
    }

    -- Text (chunked by character/token ranges)
    {
        "line_start": 100,
        "line_end": 150
    }
*/

-- Create vector similarity index for fast cosine similarity search
CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops);

-- Regular indexes for common queries
CREATE INDEX idx_chunks_file_id ON chunks(file_id);
