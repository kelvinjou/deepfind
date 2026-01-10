# This utility file is for generating text embeddings using sentence-transformers.

from sentence_transformers import SentenceTransformer
from lib.constants import EMBEDDING_MODEL, EMBEDDING_DIMENSION

# Load model once at module level for efficiency
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a single text string.

    Args:
        text: The text to embed

    Returns:
        A list of floats with length EMBEDDING_DIMENSION (512)
    """
    model = _get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a batch (more efficient).

    Args:
        texts: List of texts to embed

    Returns:
        List of embeddings, each with length EMBEDDING_DIMENSION (512)
    """
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


if __name__ == "__main__":
    # Test the embedding function
    test_texts = [
        "Hello, how are you?",
        "The quick brown fox jumps over the lazy dog.",
    ]

    embeddings = get_embeddings(test_texts)

    for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
        print(f"Text {i}: {text}")
        print(f"  Dimension: {len(emb)}")
        print(f"  First 5 values: {emb[:5]}")
        print()

    # Verify dimension matches database schema
    assert len(embeddings[0]) == EMBEDDING_DIMENSION, \
        f"Expected {EMBEDDING_DIMENSION} dimensions, got {len(embeddings[0])}"
    print(f"Embedding dimension verified: {EMBEDDING_DIMENSION}")
