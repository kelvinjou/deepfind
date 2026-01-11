# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a file-finder prototype built with an Electron frontend and a FastAPI backend. The application enables semantic search across files using embeddings and vector similarity, allowing users to find files based on natural language queries rather than just file names.

## Architecture

### Frontend (Electron + React + Vite)
- **Location**: `frontend/` directory
- **Tech Stack**: Electron, React, TypeScript, Vite, TailwindCSS v4, shadcn/ui components
- **Main Process**: `electron/main.ts` - Handles window creation and IPC handlers for file system operations
- **Preload Script**: `electron/preload.ts` - Exposes safe APIs to renderer via `contextBridge`
- **Renderer**: `src/App.tsx` - Main UI component with folder selection and search interface
- **IPC Communication**: The main process exposes file system APIs through IPC:
  - `dialog:openDirectory` - Opens directory selection dialog
  - `dialog:openFile` - Opens file selection dialog
  - `fs:readDirectory` - Reads directory contents
  - `fs:getStats` - Gets file statistics
- **API Integration**: Frontend communicates with FastAPI backend at `http://localhost:7777`:
  - `POST /dir/` - Submit folder path for processing
  - `GET /query/?q=<query>` - Query for file search results

### Backend (FastAPI)
- **Location**: `backend/` directory
- **Tech Stack**: FastAPI, Python, Uvicorn, sentence-transformers, OpenAI Whisper, BLIP (image captioning)
- **Entry Point**: `app/main.py` - Starts Uvicorn server on port 7777
- **API Setup**: `app/api.py` - FastAPI app with CORS configured for Vite dev server (port 5173)
- **Core Modules**:
  - `lib/util/db_process.py` - File processing orchestration (routes by MIME type)
  - `lib/util/folder_extraction.py` - File discovery and metadata extraction
  - `lib/util/embedding.py` - Sentence-transformer embeddings (all-mpnet-base-v2, 768 dimensions)
  - `lib/util/preprocessing/` - Format-specific processors:
    - `semantic_chunking.py` - Embedding-based text segmentation
    - `pdf.py` - PDF extraction with page tracking
    - `image.py` - BLIP image captioning
    - `audio.py` - Whisper transcription with timestamps
  - `lib/supabase/util.py` - Supabase client singleton for database operations
  - `lib/scripts/test_query.py` - Query testing and result export
  - `lib/scripts/seed_database.py` - Database population script

### Database (Supabase + PostgreSQL)
- **Location**: `supabase/` directory
- **Schema**: Two main tables with pgvector support:
  - `files` - File metadata (path, name, type, size, mime_type, file_hash, processing_status, metadata JSONB)
  - `chunks` - Content chunks with embeddings (file_id FK, chunk_index, content, embedding vector(768), chunk_metadata JSONB)
- **Vector Search**: Uses IVFFlat index with cosine similarity via `query_file_chunks()` database function
- **Deduplication**: Files are deduplicated by SHA256 hash before processing

### Data Flow
1. User selects a folder via Electron dialog
2. Frontend sends folder path to backend `/dir/` endpoint for processing
3. Backend processes files (extracts text, generates embeddings, stores in database)
4. User enters natural language query
5. Frontend queries backend `/query/` endpoint
6. Backend performs semantic search and returns ranked results

## Development Commands

### Full Stack (from project root)
```bash
# Start all services (Supabase, backend, frontend) in parallel
./run.sh
```

### Frontend (from `frontend/` directory)
```bash
npm install          # Install dependencies
npm run dev          # Run Electron app with hot reload
npm run build        # Production build (TypeScript + Vite + Electron packaging)
npm run lint         # Lint TypeScript/TSX files
```

### Backend (from `backend/` directory)
```bash
pip install -r requirements.txt    # Install Python dependencies
python -m app.main                 # Start FastAPI server on localhost:7777
# Or use: ./run_backend.sh

# Utility scripts
python -m lib.scripts.seed_database --folder test_files/ --clear  # Populate database with test files
python -m lib.scripts.test_query "your search query" --json out.json  # Test semantic search
```

### Supabase (from project root)
```bash
supabase start       # Start local Supabase (includes PostgreSQL with pgvector)
supabase stop        # Stop local Supabase
supabase db reset    # Reset database and run migrations
```

## Service Ports
| Service | Port |
|---------|------|
| FastAPI Backend | 7777 |
| Vite Dev Server | 5173 |
| Supabase API | 54321 |
| Supabase DB | 54322 |
| Supabase Studio | 54323 |

## Project-Specific Notes

### Path Resolution
- The frontend uses `@/` alias for imports, which resolves to `frontend/src/`
- Example: `import { Button } from "@/components/ui/button"`

### Electron Build Structure
```
frontend/
├── dist/              # Built renderer (web) assets
├── dist-electron/     # Built main/preload scripts
│   ├── main.js       # Main process entry point
│   └── preload.mjs   # Preload script
```

### Type Definitions
- Electron API types are defined in `src/types/electron.d.ts`
- The `window.electronAPI` global is typed with available IPC methods

### Styling
- Uses TailwindCSS v4 with Vite plugin (`@tailwindcss/vite`)
- UI components from shadcn/ui (Radix UI primitives)
- Class utilities via `clsx` and `tailwind-merge` in `src/lib/utils.ts`

### Backend CORS
- CORS is configured to accept requests from `http://localhost:5173` (Vite dev server)
- Do not change the origins in `app/api.py` unless the Vite port changes

### Backend Processing Pipeline
- Files are routed by MIME type: text files → semantic chunking, PDFs → page-aware extraction, images → BLIP captioning
- Embeddings use `all-mpnet-base-v2` model (768 dimensions) via sentence-transformers
- The embedding model and Supabase client are lazy-loaded singletons
- Chunk metadata varies by file type: PDFs include `page_start`/`page_end`, audio includes `start_time`/`end_time`

### Backend Configuration
- Environment variables in `.env`: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `POSTGRES_URL`
- Constants in `lib/constants.py`: embedding model, dimensions, audio chunk settings
