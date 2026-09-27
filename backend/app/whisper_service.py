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


def transcribe_video(video_path: str) -> str:
    model = get_model()

    segments, info = model.transcribe(
        video_path,
        beam_size=5,
    )

    transcript_parts = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            transcript_parts.append(text)

    return " ".join(transcript_parts)