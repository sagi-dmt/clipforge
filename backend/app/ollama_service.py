import json
import os
import re
from typing import Any

import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

MAX_SEGMENTS_PER_CHUNK = 30
MAX_RETRIES = 2

NUM_CTX = 2048
NUM_PREDICT = 400
TEMPERATURE = 0.2

MAX_CLIPS_PER_CHUNK = 5

# Final clip length
MIN_CLIP_DURATION = 15.0
MAX_CLIP_DURATION = 60.0
DEFAULT_CLIP_DURATION = 30.0


# ============================================================
# HELPERS
# ============================================================

def _segment_start(segment: dict[str, Any]) -> float:
    return float(
        segment.get(
            "start",
            segment.get("start_time", 0.0)
        )
    )


def _segment_end(segment: dict[str, Any]) -> float:
    return float(
        segment.get(
            "end",
            segment.get("end_time", _segment_start(segment))
        )
    )


def _segment_text(segment: dict[str, Any]) -> str:
    return str(
        segment.get(
            "text",
            segment.get("content", "")
        )
    ).strip()


def get_transcript_duration(segments: list[dict[str, Any]]) -> float:
    if not segments:
        return 0.0

    return max(_segment_end(segment) for segment in segments)


# ============================================================
# PROMPT
# ============================================================

def build_prompt(segments: list[dict[str, Any]]) -> str:
    transcript_lines = []

    for segment in segments:
        start = _segment_start(segment)
        end = _segment_end(segment)
        text = _segment_text(segment)

        if not text:
            continue

        transcript_lines.append(
            f"[{start:.2f} - {end:.2f}] {text}"
        )

    transcript = "\n".join(transcript_lines)

    return f"""
You are an AI video editor for ClipForge.

Analyze the transcript below and find the most interesting moments
that could work as short-form social media clips.

IMPORTANT:
- Do NOT create the final clip duration yourself.
- Only identify the interesting MOMENT.
- The backend will automatically expand the moment into a longer clip.
- Choose moments with strong hooks, emotion, humor, surprise,
  useful information, controversy, storytelling, or a satisfying payoff.
- Prefer moments that make sense when included inside a longer clip.
- Avoid random or meaningless sentences.
- Do not invent timestamps.
- Timestamps must be inside the transcript.
- Return between 1 and 5 strong moments.
- Each moment should normally be only a few seconds long.
- "start" and "end" identify the interesting moment, NOT the final clip.

Return ONLY valid JSON.

Required format:

{{
  "clips": [
    {{
      "start": 26.4,
      "end": 29.6,
      "title": "Countdown",
      "hook": "The moment before the big event",
      "reason": "Builds suspense and makes viewers want to see what happens"
    }}
  ]
}}

TRANSCRIPT:

{transcript}
""".strip()


def build_fallback_prompt(segments: list[dict[str, Any]]) -> str:
    transcript_lines = []

    for segment in segments:
        start = _segment_start(segment)
        end = _segment_end(segment)
        text = _segment_text(segment)

        if not text:
            continue

        transcript_lines.append(
            f"[{start:.2f} - {end:.2f}] {text}"
        )

    transcript = "\n".join(transcript_lines)

    return f"""
Find up to 5 interesting moments in this video transcript.

Pick moments that are:
- funny
- emotional
- surprising
- useful
- dramatic
- controversial
- strong story moments

Only return JSON.

Do not try to make a 15-60 second clip.
Just return the short interesting moment.

Format:

{{
  "clips": [
    {{
      "start": 10.0,
      "end": 14.0,
      "title": "Short title",
      "hook": "Interesting hook",
      "reason": "Why this moment is interesting"
    }}
  ]
}}

Use only timestamps that exist in the transcript.

TRANSCRIPT:

{transcript}
""".strip()


# ============================================================
# OLLAMA
# ============================================================

def call_ollama(prompt: str) -> str:
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

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    response_text = data.get("response", "")

    print("[Ollama] Raw model response:")
    print(response_text)

    return response_text


# ============================================================
# JSON PARSING
# ============================================================

def clean_json_text(text: str) -> str:
    text = text.strip()

    # Remove markdown code fences if model adds them
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def parse_ollama_response(response_text: str) -> list[dict[str, Any]]:
    if not response_text:
        return []

    response_text = clean_json_text(response_text)

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        print(f"[Ollama] JSON parse error: {exc}")
        return []

    if isinstance(data, list):
        clips = data

    elif isinstance(data, dict):
        if isinstance(data.get("clips"), list):
            clips = data["clips"]

        elif isinstance(data.get("result"), dict):
            clips = data["result"].get("clips", [])

        else:
            clips = []

    else:
        clips = []

    if not isinstance(clips, list):
        return []

    return clips


# ============================================================
# VALIDATE AI MOMENT
# ============================================================

def validate_ai_moment(
    clip: dict[str, Any],
    transcript_duration: float,
) -> bool:

    if not isinstance(clip, dict):
        return False

    try:
        start = float(clip["start"])
        end = float(clip["end"])
    except (KeyError, TypeError, ValueError):
        return False

    if start < 0:
        return False

    if end <= start:
        return False

    if start >= transcript_duration:
        return False

    if end > transcript_duration:
        return False

    # AI moment itself should not be absurdly long.
    # We intentionally allow short moments.
    moment_duration = end - start

    if moment_duration <= 0:
        return False

    if moment_duration > 30:
        return False

    return True


# ============================================================
# EXPAND AI MOMENT INTO REAL CLIP
# ============================================================

def expand_clip(
    clip: dict[str, Any],
    video_duration: float,
) -> dict[str, Any] | None:

    try:
        moment_start = float(clip["start"])
        moment_end = float(clip["end"])
    except (KeyError, TypeError, ValueError):
        return None

    if video_duration <= 0:
        return None

    if moment_start < 0:
        moment_start = 0.0

    if moment_end > video_duration:
        moment_end = video_duration

    if moment_end <= moment_start:
        return None

    moment_duration = moment_end - moment_start

    # ========================================================
    # CASE 1:
    # Video is shorter than minimum clip length
    # ========================================================

    if video_duration < MIN_CLIP_DURATION:
        final_start = 0.0
        final_end = video_duration

    # ========================================================
    # CASE 2:
    # Video is between 15 and 60 seconds
    # ========================================================

    elif video_duration <= MAX_CLIP_DURATION:
        final_start = 0.0
        final_end = video_duration

    # ========================================================
    # CASE 3:
    # Normal video > 60 seconds
    # ========================================================

    else:
        target_duration = DEFAULT_CLIP_DURATION

        # Put the interesting moment roughly in the middle.
        moment_center = (moment_start + moment_end) / 2.0

        final_start = moment_center - target_duration / 2.0
        final_end = final_start + target_duration

        # Keep inside video
        if final_start < 0:
            final_start = 0.0
            final_end = target_duration

        if final_end > video_duration:
            final_end = video_duration
            final_start = video_duration - target_duration

        # Safety
        final_start = max(0.0, final_start)
        final_end = min(video_duration, final_end)

    duration = final_end - final_start

    # ========================================================
    # Final duration validation
    # ========================================================

    if duration < MIN_CLIP_DURATION:
        return None

    if duration > MAX_CLIP_DURATION:
        final_end = final_start + MAX_CLIP_DURATION

        if final_end > video_duration:
            final_end = video_duration
            final_start = max(
                0.0,
                final_end - MAX_CLIP_DURATION
            )

        duration = final_end - final_start

    result = dict(clip)

    result["start"] = round(final_start, 2)
    result["end"] = round(final_end, 2)
    result["duration"] = round(duration, 2)

    return result


# ============================================================
# REMOVE DUPLICATES / HEAVY OVERLAPS
# ============================================================

def deduplicate_clips(
    clips: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    if not clips:
        return []

    # Sort by start
    clips = sorted(
        clips,
        key=lambda x: float(x.get("start", 0))
    )

    result = []

    for clip in clips:
        try:
            start = float(clip["start"])
            end = float(clip["end"])
        except (KeyError, TypeError, ValueError):
            continue

        duplicate = False

        for existing in result:
            existing_start = float(existing["start"])
            existing_end = float(existing["end"])

            overlap_start = max(start, existing_start)
            overlap_end = min(end, existing_end)

            overlap = max(0.0, overlap_end - overlap_start)

            shorter_duration = min(
                end - start,
                existing_end - existing_start
            )

            if shorter_duration > 0:
                overlap_ratio = overlap / shorter_duration

                if overlap_ratio >= 0.70:
                    duplicate = True
                    break

        if not duplicate:
            result.append(clip)

    return result


# ============================================================
# ANALYZE ONE CHUNK
# ============================================================

def analyze_chunk(
    segments: list[dict[str, Any]],
    video_duration: float,
) -> list[dict[str, Any]]:

    prompt = build_prompt(segments)

    for attempt in range(MAX_RETRIES + 1):

        print(
            f"[Ollama] Analysis attempt "
            f"{attempt + 1}/{MAX_RETRIES + 1}"
        )

        try:
            response_text = call_ollama(prompt)

            ai_clips = parse_ollama_response(response_text)

            valid_moments = []

            for clip in ai_clips:

                if validate_ai_moment(
                    clip,
                    video_duration,
                ):
                    valid_moments.append(clip)
                else:
                    print(
                        "[Ollama] Rejected invalid AI moment:"
                    )
                    print(clip)

            if valid_moments:
                final_clips = []

                for clip in valid_moments:

                    expanded = expand_clip(
                        clip,
                        video_duration,
                    )

                    if expanded:
                        final_clips.append(expanded)

                final_clips = deduplicate_clips(
                    final_clips
                )

                return final_clips[:MAX_CLIPS_PER_CHUNK]

            # =================================================
            # FALLBACK
            # =================================================

            print(
                "[Ollama] No valid moments returned. "
                "Trying fallback prompt."
            )

            fallback_prompt = build_fallback_prompt(
                segments
            )

            fallback_response = call_ollama(
                fallback_prompt
            )

            fallback_clips = parse_ollama_response(
                fallback_response
            )

            valid_fallback = []

            for clip in fallback_clips:

                if validate_ai_moment(
                    clip,
                    video_duration,
                ):
                    expanded = expand_clip(
                        clip,
                        video_duration,
                    )

                    if expanded:
                        valid_fallback.append(
                            expanded
                        )

            valid_fallback = deduplicate_clips(
                valid_fallback
            )

            if valid_fallback:
                print(
                    f"[Ollama] Fallback returned "
                    f"{len(valid_fallback)} clips"
                )

                return valid_fallback[
                    :MAX_CLIPS_PER_CHUNK
                ]

            print(
                "[Ollama] Fallback returned "
                "0 valid clips"
            )

        except Exception as exc:
            print(
                f"[Ollama] Attempt failed: {exc}"
            )

    return []


# ============================================================
# MAIN ANALYSIS FUNCTION
# ============================================================

def analyze_transcript(
    segments: list[dict[str, Any]]
) -> dict[str, Any]:

    if not segments:
        raise RuntimeError(
            "No transcript segments available."
        )

    video_duration = get_transcript_duration(
        segments
    )

    if video_duration <= 0:
        raise RuntimeError(
            "Could not determine video duration."
        )

    print(
        f"[Ollama] Starting analysis. "
        f"Transcript duration: {video_duration:.2f}s"
    )

    # ========================================================
    # CHUNK TRANSCRIPT
    # ========================================================

    chunks = [
        segments[i:i + MAX_SEGMENTS_PER_CHUNK]
        for i in range(
            0,
            len(segments),
            MAX_SEGMENTS_PER_CHUNK
        )
    ]

    all_clips = []

    for index, chunk in enumerate(chunks):

        print(
            f"[Ollama] Processing chunk "
            f"{index + 1}/{len(chunks)}"
        )

        chunk_clips = analyze_chunk(
            chunk,
            video_duration,
        )

        print(
            f"[Ollama] Chunk {index + 1}/"
            f"{len(chunks)} returned "
            f"{len(chunk_clips)} valid clips"
        )

        all_clips.extend(chunk_clips)

    # ========================================================
    # FINAL DEDUPLICATION
    # ========================================================

    final_clips = deduplicate_clips(
        all_clips
    )

    # Sort by start time
    final_clips = sorted(
        final_clips,
        key=lambda x: float(x["start"])
    )

    print(
        f"[Ollama] Analysis complete. "
        f"Found {len(final_clips)} valid unique clips."
    )

    if not final_clips:
        raise RuntimeError(
            "Ollama completed, but no valid clips were generated."
        )

    return {
        "clips": final_clips
    }