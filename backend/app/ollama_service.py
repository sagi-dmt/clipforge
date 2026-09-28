import json
import os
import urllib.request

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Keep each request comfortably below Ollama's current context limit.
MAX_SEGMENTS_PER_CHUNK = 40


def call_ollama(transcript_segments):
    prompt = """
You are an AI clip editor for short-form videos.

Analyze the transcript segments below and find the best moments that could become viral short clips.

For every clip:
- Choose a strong beginning and ending timestamp.
- Prefer humor, surprise, conflict, emotion, interesting statements, reactions, or a strong hook.
- Avoid boring setup and unnecessary pauses.
- Clips should generally be between 15 and 60 seconds.
- Do not invent anything that is not present in the transcript.

Return ONLY valid JSON in this exact format:

{
  "clips": [
    {
      "start": 0.0,
      "end": 30.0,
      "title": "Short descriptive title",
      "hook": "A short hook for the clip",
      "reason": "Why this moment would work well as a short"
    }
  ]
}

Return as many good clips as you can find in this section.

Transcript:
"""

    prompt += "\n".join(
        f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}"
        for segment in transcript_segments
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))

    return json.loads(result["response"])


def analyze_transcript(transcript_segments):
    """
    Analyze the entire transcript in multiple chunks so long videos
    are not truncated by Ollama.
    """

    all_clips = []

    total_segments = len(transcript_segments)

    print(
        f"[Ollama] Analyzing {total_segments} transcript segments"
    )

    for i in range(0, total_segments, MAX_SEGMENTS_PER_CHUNK):
        chunk = transcript_segments[
            i:i + MAX_SEGMENTS_PER_CHUNK
        ]

        chunk_number = (
            i // MAX_SEGMENTS_PER_CHUNK
        ) + 1

        total_chunks = (
            (total_segments + MAX_SEGMENTS_PER_CHUNK - 1)
            // MAX_SEGMENTS_PER_CHUNK
        )

        print(
            f"[Ollama] Processing chunk "
            f"{chunk_number}/{total_chunks} "
            f"({len(chunk)} segments)"
        )

        try:
            result = call_ollama(chunk)

            clips = result.get("clips", [])

            print(
                f"[Ollama] Chunk {chunk_number} found "
                f"{len(clips)} clips"
            )

            all_clips.extend(clips)

        except Exception as exc:
            print(
                f"[Ollama] Chunk {chunk_number} failed: "
                f"{exc}"
            )

    # Remove obvious duplicate clips.
    unique_clips = []

    for clip in all_clips:
        duplicate = False

        for existing in unique_clips:
            if (
                abs(
                    float(clip["start"])
                    - float(existing["start"])
                ) < 2
                and
                abs(
                    float(clip["end"])
                    - float(existing["end"])
                ) < 2
            ):
                duplicate = True
                break

        if not duplicate:
            unique_clips.append(clip)

    print(
        f"[Ollama] Analysis complete. "
        f"Found {len(unique_clips)} unique clips."
    )

    return {
        "clips": unique_clips
    }