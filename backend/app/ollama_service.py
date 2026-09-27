import json
import os
import urllib.request


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def analyze_transcript(transcript_segments):
    prompt = """
You are an AI clip editor for short-form videos.

Analyze the transcript segments below and find the best moments that could become viral short clips.

For every clip:
- Choose a strong beginning and ending timestamp.
- Prefer moments with humor, surprise, conflict, emotion, interesting statements, reactions, or a strong hook.
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

Return 3 to 5 clips when enough good moments exist.

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

    response_text = result["response"]

    return json.loads(response_text)