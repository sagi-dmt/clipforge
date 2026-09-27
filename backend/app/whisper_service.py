from faster_whisper import WhisperModel


_model = None


def get_model():
    global _model

    if _model is None:
        _model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",
        )

    return _model


def transcribe_video(video_path: str):
    model = get_model()

    segments, info = model.transcribe(
        video_path,
        beam_size=5,
    )

    transcript_parts = []
    transcript_segments = []

    for segment in segments:
        text = segment.text.strip()

        if not text:
            continue

        transcript_parts.append(text)

        transcript_segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": text,
        })

    return {
        "text": " ".join(transcript_parts),
        "segments": transcript_segments,
    }