from util.audio import transcribe_audio
from util.embedding import get_embeddings
from pydantic import FilePath

# 1. Transcribe audio
print("=== Transcribing audio ===")
test_file = FilePath("/Users/anarang/Projects/file-finder-prototype/backend/test_files/audio/test1.ogg")
chunks = transcribe_audio(test_file)
print(f"Created {len(chunks)} chunks\n")

# 2. Create embeddings for each chunk
print("=== Creating embeddings ===")
texts = [chunk["content"] for chunk in chunks]
embeddings = get_embeddings(texts)

# 3. Show results
for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
    meta = chunk["chunk_metadata"]
    print(f"Chunk {i}: {meta['start_time']:.1f}s - {meta['end_time']:.1f}s")
    print(f"  Content: {chunk['content'][:80]}...")
    print(f"  Embedding dim: {len(emb)}, first 3 values: {emb[:3]}")
    print()

print("Done!")
