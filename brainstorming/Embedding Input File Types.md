# Embedding Input File Types

- .pdf
    - Two step process:
        1. Scan for text
            1. Use OCR tool or some text scanning tool to find all text
            2. Chunk text based on some rule for each ENTIRE pdf
        2. Scan for images
            1. Convert each page into an image
            2. Prompt GPT for each page image → “Are there any images, diagrams, charts, etc. If so summarize what type of image it is and describe what it is conveying…”
- any image file (.png, .webp, .jpeg, etc.)
- text files (.txt, .py, .cpp, etc.)
- audio files (.mp3, etc.)

Sources:

[https://supabase.com/docs/guides/ai/vector-columns](https://supabase.com/docs/guides/ai/vector-columns)

use cosine similarity to query