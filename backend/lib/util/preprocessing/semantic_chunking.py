#!/usr/bin/env python3


from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import os
import numpy as np

# -------- Sentence splitting --------
import nltk
nltk.download("punkt_tab", quiet=True)

# -------- Embeddings --------


def read_txt_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def semantic_chunk_text(
    text: str,
    model_name: str = "all-MiniLM-L6-v2",
    similarity_threshold: float = 0.7,
    min_sentences_per_chunk: int = 4,
    max_sentences_per_chunk: int = 20,
    overlap_sentences: int = 0,
    shift_patience: int = 2,
    debug_info: list = None,
) -> list[str]:
    """
    Returns a list of semantically coherent text chunks.
    Uses chunk-centroid similarity and persistent topic shift detection.
    """

    # 1. Sentence split
    sentences = sent_tokenize(text)
    if not sentences:
        return []

    # 2. Load local embedding model
    model = SentenceTransformer(model_name)

    # 3. Embed sentences
    embeddings = model.encode(
        sentences,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )

    chunks = []
    current_chunk = [sentences[0]]
    current_embeddings = [embeddings[0]]
    previous_chunk_sentences = []

    similarities = []
    shift_count = 0

    for i in range(1, len(sentences)):
        # Compute centroid of current chunk
        centroid = np.mean(current_embeddings, axis=0)
        similarity = float(np.dot(centroid, embeddings[i]))
        similarities.append(similarity)

        should_consider_split = (
            similarity < similarity_threshold
            and len(current_chunk) >= min_sentences_per_chunk
        )

        if should_consider_split:
            shift_count += 1
        else:
            shift_count = 0

        # Final split decision
        if (
            shift_count >= shift_patience
            or len(current_chunk) >= max_sentences_per_chunk
        ):
            chunks.append(" ".join(current_chunk))

            # Overlap handling
            previous_chunk_sentences = (
                current_chunk[-overlap_sentences:]
                if overlap_sentences > 0
                else []
            )
            previous_chunk_embeddings = (
                current_embeddings[-overlap_sentences:]
                if overlap_sentences > 0
                else []
            )

            current_chunk = previous_chunk_sentences.copy()
            current_embeddings = previous_chunk_embeddings.copy()
            shift_count = 0

        current_chunk.append(sentences[i])
        current_embeddings.append(embeddings[i])

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

    # Debug output
    if similarities and debug_info is not None:
        debug_info.append(
            f"Similarity stats: min={min(similarities):.3f}, "
            f"max={max(similarities):.3f}, "
            f"avg={np.mean(similarities):.3f}"
        )
        debug_info.append(
            f"Sentences below threshold: "
            f"{sum(1 for s in similarities if s < similarity_threshold)} "
            f"/ {len(similarities)}"
        )

    return chunks


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Semantic text chunking")
    parser.add_argument("input_file", help="Path to input text file")
    parser.add_argument(
        "-o", "--output", help="Path to output file (optional)")
    parser.add_argument("--overlap", type=int, default=2,
                        help="Number of sentences to overlap between chunks (default: 0)")
    parser.add_argument("--threshold", type=float, default=0.7,
                        help="Similarity threshold (default: 0.7)")
    parser.add_argument("--min-sentences", type=int, default=4,
                        help="Minimum sentences per chunk (default: 4)")
    parser.add_argument("--max-sentences", type=int, default=20,
                        help="Maximum sentences per chunk (default: 20)")

    args = parser.parse_args()

    text = read_txt_file(args.input_file)

    # Collect debug info
    debug_info = []
    chunks = semantic_chunk_text(
        text,
        similarity_threshold=args.threshold,
        min_sentences_per_chunk=args.min_sentences,
        max_sentences_per_chunk=args.max_sentences,
        overlap_sentences=args.overlap,
        debug_info=debug_info
    )

    output_lines = []

    # Add debug info first
    if debug_info:
        output_lines.extend(debug_info)
        output_lines.append("")

    output_lines.append(f"Generated {len(chunks)} semantic chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        output_lines.append(f"{'-'*80}")
        output_lines.append(f"Chunk {i}")
        output_lines.append(f"{'-'*80}")
        output_lines.append(chunk)
        output_lines.append("")

    output_text = "\n".join(output_lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Output written to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
