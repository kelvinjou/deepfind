-- Files table: metadata about uploaded files
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'image', 'text', 'pdf', 'audio'
    file_size BIGINT, -- size in bytes
    mime_type TEXT NOT NULL, -- e.g., 'image/png', 'application/pdf'
    file_hash TEXT UNIQUE NOT NULL,  -- to avoid duplicate uploads
    last_modified_at TIMESTAMP NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    metadata JSONB NOT NULL  -- store file-specific metadata (dimensions for images, duration for audio, etc.)
);

/*
    metadata examples for each file type:

    -- Image
    {
        "width": 1920,
        "height": 1080,
        "format": "JPEG"
    }

    -- Audio
    {
        "duration_seconds": 245.5,
        "format": "mp3"
    }

    -- PDF
    {
        "total_pages": 50,
        "has_images": true,
        "image_count": 12
    }

    -- Text
    {
        "line_count": 1500,
        "format": "markdown"  -- could also be 'plain', 'html', 'python', etc.
    }
*/

-- Regular indexes for common queries
CREATE INDEX idx_files_type ON files(file_type);
