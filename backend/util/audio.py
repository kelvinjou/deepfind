# This utility file is for processing audio files.
# The goal is to take in an audio file and return a transcription of the audio (with OpenAI Whisper), including timestamps.

from lib.constants import AUDIO_OVERLAP_DURATION_SEC, AUDIO_TARGET_DURATION_SEC
import whisper
from pydantic import FilePath
from dataclasses import dataclass


@dataclass
class TranscriptChunk:
    """Represents a chunk of transcript with timestamp metadata."""
    content: str  # Includes overlapping context from adjacent chunks
    start_time: float  # Start of the true (non-overlapping) content
    end_time: float  # End of the true (non-overlapping) content
    chunk_index: int


def _get_audio_transcript(file_path: FilePath) -> dict:
    print(whisper.available_models())
    model = whisper.load_model("base")
    result = model.transcribe(str(file_path))
    return result


def _chunk_transcript(
    transcription: dict,
    target_duration_seconds: float = 45.0,
    overlap_duration_seconds: float = 10.0,
) -> list[TranscriptChunk]:
    """
    Chunk a Whisper transcription into overlapping segments for vector database storage.

    Strategy:
    - Uses Whisper segments as atomic units (never splits mid-segment to preserve sentence boundaries)
    - Groups segments into chunks of approximately target_duration_seconds
    - Creates overlap by including text from adjacent chunks for context
    - Timestamps reflect only the true (non-overlapping) content section

    Args:
        transcription: Whisper transcription result with 'segments' key
        target_duration_seconds: Target duration for each chunk (default 45s, good for ~200-300 words)
        overlap_duration_seconds: How much audio to overlap between chunks (default 10s)

    Returns:
        List of TranscriptChunk objects where:
        - content: includes overlapping text for context
        - start_time/end_time: timestamps for the true (non-overlapping) section
    """
    segments = transcription.get("segments", [])
    if not segments:
        return []

    chunks: list[TranscriptChunk] = []
    current_segments: list[dict] = []
    current_duration = 0.0
    chunk_index = 0

    # Track overlap segments from previous chunk
    overlap_segments: list[dict] = []

    i = 0
    while i < len(segments):
        segment = segments[i]
        segment_duration = segment["end"] - segment["start"]

        # Add segment to current chunk
        current_segments.append(segment)
        current_duration += segment_duration

        # Check if we've reached target duration
        if current_duration >= target_duration_seconds:
            # Create chunk with overlap from previous chunk prepended
            chunk = _create_chunk(
                overlap_segments + current_segments,
                chunk_index,
                overlap_start_index=len(overlap_segments),
            )
            chunks.append(chunk)
            chunk_index += 1

            # Determine overlap segments for next chunk
            # Walk backwards from end of current_segments until we have ~overlap_duration
            overlap_segments = _get_overlap_segments(
                current_segments, overlap_duration_seconds)

            # Reset for next chunk
            current_segments = []
            current_duration = 0.0

        i += 1

    # Handle remaining segments
    if current_segments:
        chunk = _create_chunk(
            overlap_segments + current_segments,
            chunk_index,
            overlap_start_index=len(overlap_segments),
        )
        chunks.append(chunk)

    return chunks


def _create_chunk(
    chunk_segments: list[dict],
    chunk_index: int,
    overlap_start_index: int,
) -> TranscriptChunk:
    """Create a TranscriptChunk from a list of segments."""
    if not chunk_segments:
        raise ValueError("Cannot create chunk from empty segments")

    # Content includes overlap for context
    content = " ".join(seg["text"].strip() for seg in chunk_segments)

    # Timestamps are for the true (non-overlapping) section only
    true_start_time = chunk_segments[overlap_start_index]["start"] if overlap_start_index < len(
        chunk_segments) else chunk_segments[0]["start"]

    return TranscriptChunk(
        content=content,
        start_time=true_start_time,
        end_time=chunk_segments[-1]["end"],
        chunk_index=chunk_index,
    )


def _get_overlap_segments(segments: list[dict], target_overlap_duration: float) -> list[dict]:
    """Get segments from end of list that sum to approximately target_overlap_duration."""
    if not segments:
        return []

    overlap_segments = []
    accumulated_duration = 0.0

    # Walk backwards through segments, accumulating until we reach target duration
    for seg in reversed(segments):
        seg_duration = seg["end"] - seg["start"]
        overlap_segments.insert(0, seg)
        accumulated_duration += seg_duration

        # Stop once we've accumulated enough overlap
        if accumulated_duration >= target_overlap_duration:
            break

    return overlap_segments


def _chunks_to_json(chunks: list[TranscriptChunk]) -> list[dict]:
    """
    Convert TranscriptChunks to the format expected by the database.

    Returns list of dicts with:
    - content: str (the text, includes overlapping context)
    - chunk_index: int
    - chunk_metadata: dict with timestamp info for the true (non-overlapping) section
    """
    return [
        {
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "chunk_metadata": {
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
            },
        }
        for chunk in chunks
    ]


def transcribe_audio(file_path: FilePath) -> dict:
    transcription = _get_audio_transcript(file_path)

    # Chunk the transcript
    chunks = _chunk_transcript(
        transcription,
        target_duration_seconds=AUDIO_TARGET_DURATION_SEC,  # ~60 second chunks
        overlap_duration_seconds=AUDIO_OVERLAP_DURATION_SEC,  # ~15 second overlap
    )

    # Convert to database format
    db_chunks = _chunks_to_json(chunks)

    return db_chunks


if __name__ == "__main__":
    test_file = FilePath(
        "/Users/anarang/Projects/file-finder-prototype/backend/test_files/audio/test1.ogg")
    result = transcribe_audio(test_file)

    # print as json
    import json
    print(json.dumps(result, indent=2))
