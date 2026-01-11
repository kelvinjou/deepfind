AUDIO_TARGET_DURATION_SEC = 60  # 60 second chunks
AUDIO_OVERLAP_DURATION_SEC = 15  # 15 second overlap

DEFAULT_MATCH_THRESHOLD = 0.1  # Lowered threshold for broader matches

EMBEDDING_MODEL = "all-mpnet-base-v2"  # Highest quality English model
EMBEDDING_DIMENSION = 768

SUPPORTED_MIME_TYPES = {
    # Text
    'text/plain',
    # PDF
    'application/pdf',
    # Audio
    'audio/mpeg',      # .mp3
    'audio/wav',       # .wav
    'audio/x-wav',     # .wav (alternate)
    'audio/ogg',       # .ogg
    'audio/flac',      # .flac
    'audio/mp4',       # .m4a
    'audio/x-m4a',     # .m4a (alternate)
    # Images
    'image/jpeg',      # .jpeg, .jpg
    'image/png',       # .png
    'image/webp',      # .webp
}
