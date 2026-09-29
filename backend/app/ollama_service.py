import json
import os
import time
import urllib.error
import urllib.request


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b",
)

# Keep chunks small enough for the 4096 context model.
MAX_SEGMENTS_PER_CHUNK = 30

# Maximum number of retry attempts for one chunk.
MAX_RETRIES = 2

# Ollama generation settings.
NUM_CTX = 2048
NUM_PREDICT = 350
TEMPERATURE = 0.2

# We only want a small number of useful suggestions from each chunk.
MAX_CLIPS_PER_CHUNK = 5


def build_prompt(transcript_segments):
    """
    Build the prompt sent to Ollama.
    """

    transcript = "\n".join(
        f"[{segment['start']:.2f}s - {segment['end']:.2f}s] "
        f"{segment['text']}"
        for segment in transcript_segments
    )

    return f"""
You are an AI clip editor for short-form videos.

Analyze the transcript below and find the strongest moments that could
work as short-form video clips.

IMPORTANT RULES:

- Return EXACTLY 3 to 5 clips when enough good moments exist.
- NEVER return more than 5 clips.
- Every clip MUST be between 15 and 60 seconds long.
- Use ONLY timestamps that exist in the transcript.
- Do NOT invent events, dialogue, or timestamps.
- Prefer humor, surprise, conflict, emotion, interesting statements,
  strong opinions, reactions, useful information, or strong hooks.
- Avoid boring introductions, greetings, silence, and unnecessary setup.
- Each clip should make sense when watched by itself.
- Choose strong beginnings and endings.
- Do not create multiple nearly identical clips.

RETURN ONLY VALID JSON.

Use EXACTLY this format:

{{
  "clips": [
    {{
      "start": 10.0,
      "end": 35.0,
      "title": "Short descriptive title",
      "hook": "A short hook describing why someone would keep watching",
      "reason": "Why this moment works well as a short clip"
    }}
  ]
}}

Do not write anything before or after the JSON.

Transcript:

{transcript}
"""


def validate_clip(clip):
    """
    Validate and normalize one AI-generated clip.
    Returns None when the clip is invalid.
    """

    if not isinstance(clip, dict):
        return None

    try:
        start = float(clip.get("start"))
        end = float(clip.get("end"))
    except (TypeError, ValueError):
        return None

    if not start >= 0:
        return None

    if not end > start:
        return None

    duration = end - start

    # Shorts should generally be 15-60 seconds.
    if duration < 15:
        return None

    if duration > 60:
        return None

    title = str(
        clip.get("title")
        or clip.get("name")
        or "AI Suggested Clip"
    ).strip()

    hook = str(
        clip.get("hook")
        or clip.get("description")
        or ""
    ).strip()

    reason = str(
        clip.get("reason")
        or clip.get("explanation")
        or ""
    ).strip()

    return {
        "start": round(start, 2),
        "end": round(end, 2),
        "title": title,
        "hook": hook,
        "reason": reason,
    }


def parse_ollama_response(response_text):
    """
    Parse Ollama's JSON response safely.

    Ollama normally returns a JSON string inside:
        result["response"]

    We support:
        {"clips": [...]}
        [...]
        {"result": {"clips": [...]}}
    """

    if not response_text:
        raise ValueError("Ollama returned an empty response.")

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Ollama returned invalid JSON: {exc}"
        ) from exc

    clips = []

    if isinstance(data, list):
        clips = data

    elif isinstance(data, dict):
        if isinstance(data.get("clips"), list):
            clips = data["clips"]

        elif isinstance(data.get("result"), dict):
            if isinstance(data["result"].get("clips"), list):
                clips = data["result"]["clips"]

    if not isinstance(clips, list):
        raise ValueError(
            "Ollama JSON did not contain a valid 'clips' array."
        )

    valid_clips = []

    for clip in clips:
        normalized = validate_clip(clip)

        if normalized is not None:
            valid_clips.append(normalized)

    # Never allow more than the requested maximum.
    return valid_clips[:MAX_CLIPS_PER_CHUNK]


def call_ollama(transcript_segments):
    """
    Send one transcript chunk to Ollama.
    """

    prompt = build_prompt(transcript_segments)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "temperature": TEMPERATURE,
        },
    }

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=300,
    ) as response:
        raw_response = response.read().decode("utf-8")

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Ollama HTTP response was not valid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "Ollama returned an unexpected response format."
        )

    if "error" in result:
        raise RuntimeError(
            f"Ollama error: {result['error']}"
        )

    response_text = result.get("response")

    if not response_text:
        raise ValueError(
            "Ollama response did not contain a 'response' field."
        )

    return parse_ollama_response(response_text)


def analyze_chunk_with_retry(
    chunk,
    chunk_number,
    total_chunks,
):
    """
    Analyze one chunk with retries.
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):
        print(
            f"[Ollama] Chunk "
            f"{chunk_number}/{total_chunks} "
            f"attempt {attempt}/{MAX_RETRIES + 1}"
        )

        try:
            clips = call_ollama(chunk)

            print(
                f"[Ollama] Chunk "
                f"{chunk_number}/{total_chunks} returned "
                f"{len(clips)} valid clips"
            )

            return clips

        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ValueError,
            RuntimeError,
            json.JSONDecodeError,
        ) as exc:

            last_error = exc

            print(
                f"[Ollama] Chunk "
                f"{chunk_number}/{total_chunks} failed: "
                f"{exc}"
            )

            if attempt <= MAX_RETRIES:
                time.sleep(1)

    print(
        f"[Ollama] Chunk "
        f"{chunk_number}/{total_chunks} failed after "
        f"{MAX_RETRIES + 1} attempts."
    )

    return []


def remove_duplicate_clips(clips):
    """
    Remove clips that have almost identical timestamps.
    """

    unique_clips = []

    for clip in clips:
        duplicate = False

        for existing in unique_clips:
            start_difference = abs(
                float(clip["start"])
                - float(existing["start"])
            )

            end_difference = abs(
                float(clip["end"])
                - float(existing["end"])
            )

            if (
                start_difference < 3
                and end_difference < 3
            ):
                duplicate = True
                break

        if not duplicate:
            unique_clips.append(clip)

    return unique_clips


def analyze_transcript(transcript_segments):
    """
    Analyze the complete transcript in multiple chunks.

    Returns:

    {
        "clips": [...]
    }
    """

    if not transcript_segments:
        raise ValueError(
            "Transcript contains no segments."
        )

    total_segments = len(transcript_segments)

    print(
        f"[Ollama] Starting transcript analysis: "
        f"{total_segments} segments"
    )

    all_clips = []

    total_chunks = (
        total_segments + MAX_SEGMENTS_PER_CHUNK - 1
    ) // MAX_SEGMENTS_PER_CHUNK

    for i in range(
        0,
        total_segments,
        MAX_SEGMENTS_PER_CHUNK,
    ):
        chunk = transcript_segments[
            i:i + MAX_SEGMENTS_PER_CHUNK
        ]

        chunk_number = (
            i // MAX_SEGMENTS_PER_CHUNK
        ) + 1

        print(
            f"[Ollama] Processing chunk "
            f"{chunk_number}/{total_chunks} "
            f"with {len(chunk)} transcript segments"
        )

        clips = analyze_chunk_with_retry(
            chunk,
            chunk_number,
            total_chunks,
        )

        all_clips.extend(clips)

    # Remove duplicate suggestions.
    unique_clips = remove_duplicate_clips(
        all_clips
    )

    # Final validation.
    final_clips = []

    for clip in unique_clips:
        normalized = validate_clip(clip)

        if normalized is not None:
            final_clips.append(normalized)

    print(
        f"[Ollama] Analysis complete. "
        f"Found {len(final_clips)} valid unique clips."
    )

    # IMPORTANT:
    # Do not silently pretend that analysis succeeded
    # when Ollama produced absolutely nothing.
    if not final_clips:
        raise RuntimeError(
            "Ollama completed, but no valid clips were generated."
        )

    return {
        "clips": final_clips
    }