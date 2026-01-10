# SBHacks Idealization ‘26

### Hierarchal File Directory Queries

### User Story

1. Open the desktop app + give permissions to access your files
2. Then, you click a button and it prompts you to select all folders/files you want to store
3. Once selected, it goes through all files and processes them through a pipeline we create - stores embeddings + metadata
   1. This desktop app checks for changes with a hash (upsert)
      1. if file(s) are changed, then update embedding
      2. if path doesn’t even exist, then remove embedding
   2. Since these embeddings are stored in cloud, we can also allow user to access their files from different devices, running the embeddings model on the device itself
4. Once files are uploaded and indexed, the user is able to search
   1. User can choose which device(s) to search from, since different devices are stored separately
   2. what if we’re able to automate a workflow where the user who doesn’t have direct access to their PC (with the files contained on it) and have our app search query and send it to them via email or smth

### General Ideas

vecdb, RAG lookup

i.e. “create a folder in Downloads directory with all of my resumes (they’re scattered across the file system)”

can run in the cloud and can be accessed from any device (I rlly like this idea - KJ)

model runs on the device, data is stored in the cloud → (maybe Chroma Cloud?)

possibly use encryption? (security aspect)

### Tech Stack

Vector embeddings: OpenAI Embeddings

ChromaDB (this one’s open source, free for local), Pinecone for vecdb

alternative: pgvector, [sqlite-vss](https://github.com/asg017/sqlite-vss?ref=gettingstarted.ai) which enable vector storage for traditional sql

**look into pgvector and S3 Vectors Wrapper**

If we go in the direction of a Mac app, we could use Tauri/[Electron](https://www.electronforge.io/guides/framework-integration/react-with-typescript) (TS-based, might be easier for ygs. Shadcn might look better than Apple native UI) or SwiftUI

PDF/text files: OpenAI text-embedding-3 (paid) or [all-miniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (open source on HuggingFace)

Image to vector embedding: use [OpenAI CLIP](https://huggingface.co/openai/clip-vit-base-patch32) (open source)

videos: OpenAI CLIP (but parsed by frame)

will need zero-shot classification for captioning visual assets

for getting key frames from videos:

- Video-KF (Python): CLI tool and library for extracting representative keyframes based on the video's original encoding (I-frames)
  - I think this uses built-in i-frames, will need to generate every few seconds basically but might be smth worth if videos aren’t egregiously long?
- [\*\*Video-Keyframe-Detector](https://github.com/joelibaceta/video-keyframe-detector):\*\* this is a library that uses some heuristics to find key frames
- **Katna:** library for "smart" frame extraction. It uses a combination of criteria like sharpness, brightness, and entropy to filter out bad frames (blurry, too dark) and keep the most visually interesting ones
- [\*\*Kive.ai](https://kive.ai/tools/extract-frames-from-video):\*\*  AI-powered web tool that automatically analyzes video content to pull the "best" frames from every scene using proprietary machine learning models
- [\*\*BestFrame](https://ulti.media/bestframe/):\*\* Analyzes video clips to find the "BestFrame" based on temporal sorting and content quality thresholds

Probably best to use CLIP for everything and not use SBERT for text stuff since using diff vector embedding models will probably cause discrepancies when we compare distances

(Or probably use a hybrid of both)

- weigh advantages/disadvantages with pgvector, chromadb, S3 vector wrapper, pinecone
- zero-shot classification captioning for images
- top 4 impact frames of a video, frame parsed into CLIP or some OCR → turn into captioning
- openAI whisper for spoken audio VS instrumental (?)
- Look into Electron
- think about processing pipeline
  - chunking? MB size limit? etc.

MCP functions for automating file collection (i.e. making a new directory with the selected items, or summary of files on a specified topic)

For example, for Move, make sure to show file preview of selected, and you just drag, move.

Chunking, no summary, store each chunk as vector into pgvec. For search (you can then see the highlighted “chunk” like google search)
