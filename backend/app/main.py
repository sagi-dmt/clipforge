from pathlib import Path
from uuid import uuid4
import shutil
import subprocess

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, get_db
from app.models import Clip, Project, User, Video
from app.whisper_service import transcribe_video
from app.ollama_service import analyze_transcript


# ============================================================
# APP
# ============================================================

app = FastAPI(title="ClipForge API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STORAGE
# ============================================================

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# MODELS
# ============================================================

class ProjectCreate(BaseModel):
    name: str
    user_id: str


# ============================================================
# HELPERS
# ============================================================

def clip_to_dict(clip: Clip):
    return {
        "clip_id": clip.id,
        "id": clip.id,
        "project_id": clip.project_id,
        "video_id": clip.video_id,
        "filename": clip.filename,
        "storage_path": clip.storage_path,
        "start": clip.start_time,
        "end": clip.end_time,
        "duration": clip.duration,
        "created_at": clip.created_at,
        "url": (
            f"/projects/{clip.project_id}/clips/"
            f"{clip.filename}"
        ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "ClipForge",
        "status": "online",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


# ============================================================
# PROJECTS
# ============================================================

@app.get("/projects")
def get_projects(
    user_id: str,
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project)
        .filter(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return [
        {
            "id": project.id,
            "name": project.name,
            "user_id": project.user_id,
            "created_at": project.created_at,
        }
        for project in projects
    ]


@app.post("/projects")
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == project_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    project = Project(
        user_id=user.id,
        name=project_data.name,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "user_id": project.user_id,
        "created_at": project.created_at,
    }


@app.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    project_dir = UPLOAD_DIR / project_id

    try:
        if project_dir.exists():
            shutil.rmtree(project_dir)

        db.delete(project)
        db.commit()

        return {
            "success": True,
            "message": "Project deleted successfully",
            "project_id": project_id,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Project deletion failed: {str(e)}",
        )


# ============================================================
# VIDEOS
# ============================================================

@app.get("/projects/{project_id}/videos")
def get_project_videos(
    project_id: str,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    videos = (
        db.query(Video)
        .filter(Video.project_id == project_id)
        .order_by(Video.created_at.desc())
        .all()
    )

    return [
        {
            "id": video.id,
            "project_id": video.project_id,
            "filename": video.filename,
            "storage_path": video.storage_path,
            "processing_status": video.processing_status,
            "transcript": video.transcript,
            "transcript_segments": video.transcript_segments,
            "processing_error": video.processing_error,
            "created_at": video.created_at,
        }
        for video in videos
    ]


@app.delete("/projects/{project_id}/videos/{video_id}")
def delete_video(
    project_id: str,
    video_id: str,
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.project_id == project_id,
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    video_path = Path(video.storage_path)

    try:
        # Delete generated clip files.
        clips = (
            db.query(Clip)
            .filter(
                Clip.video_id == video_id,
                Clip.project_id == project_id,
            )
            .all()
        )

        for clip in clips:
            clip_path = Path(clip.storage_path)

            if clip_path.exists():
                clip_path.unlink()

        # Delete uploaded source video.
        if video_path.exists():
            video_path.unlink()

        db.delete(video)
        db.commit()

        return {
            "success": True,
            "message": "Video and generated clips deleted successfully",
            "video_id": video_id,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Video deletion failed: {str(e)}",
        )


# ============================================================
# GENERATED CLIPS - LOAD FROM DATABASE
# ============================================================

@app.get("/projects/{project_id}/clips")
def get_project_clips(
    project_id: str,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    clips = (
        db.query(Clip)
        .filter(Clip.project_id == project_id)
        .order_by(Clip.created_at.desc())
        .all()
    )

    # Remove database records whose files no longer exist.
    valid_clips = []

    for clip in clips:
        if Path(clip.storage_path).exists():
            valid_clips.append(clip)
        else:
            db.delete(clip)

    if len(valid_clips) != len(clips):
        db.commit()

    return [
        clip_to_dict(clip)
        for clip in valid_clips
    ]


# ============================================================
# WHISPER TRANSCRIPTION
# ============================================================

def process_video(video_id: str):
    db = SessionLocal()

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )

        if not video:
            print(
                f"[Whisper] Video not found: {video_id}"
            )
            return

        video.processing_status = "processing"
        video.processing_error = None

        db.commit()

        print(
            f"[Whisper] Starting transcription: "
            f"{video.filename}"
        )

        result = transcribe_video(video.storage_path)

        video.transcript = result["text"]
        video.transcript_segments = result["segments"]
        video.processing_status = "completed"
        video.processing_error = None

        db.commit()

        print(
            f"[Whisper] Completed: "
            f"{video.filename}"
        )

        print(
            f"[Whisper] Segments: "
            f"{len(result['segments'])}"
        )

    except Exception as e:
        print(
            f"[Whisper] Error: {e}"
        )

        try:
            video = (
                db.query(Video)
                .filter(Video.id == video_id)
                .first()
            )

            if video:
                video.processing_status = "failed"
                video.processing_error = str(e)

                db.commit()

        except Exception as db_error:
            print(
                "[Whisper] Failed to save error: "
                f"{db_error}"
            )

    finally:
        db.close()


# ============================================================
# UPLOAD VIDEO
# ============================================================

@app.post("/projects/{project_id}/videos")
async def upload_video(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided",
        )

    allowed_extensions = {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".m4v",
    }

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format",
        )

    video_id = str(uuid4())

    project_dir = UPLOAD_DIR / project_id

    project_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_filename = f"{video_id}{extension}"

    storage_path = project_dir / stored_filename

    try:
        with storage_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        video = Video(
            id=video_id,
            project_id=project_id,
            filename=original_name,
            storage_path=str(storage_path),
            processing_status="pending",
        )

        db.add(video)
        db.commit()
        db.refresh(video)

        background_tasks.add_task(
            process_video,
            video.id,
        )

        return {
            "id": video.id,
            "project_id": video.project_id,
            "filename": video.filename,
            "storage_path": video.storage_path,
            "processing_status": video.processing_status,
            "transcript": video.transcript,
            "transcript_segments": video.transcript_segments,
            "processing_error": video.processing_error,
            "created_at": video.created_at,
        }

    except Exception as e:
        if storage_path.exists():
            storage_path.unlink()

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Video upload failed: {str(e)}",
        )

    finally:
        await file.close()


# ============================================================
# AI VIDEO ANALYSIS
# ============================================================

@app.post(
    "/projects/{project_id}/videos/{video_id}/analyze"
)
def analyze_video(
    project_id: str,
    video_id: str,
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.project_id == project_id,
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    if not video.transcript_segments:
        raise HTTPException(
            status_code=400,
            detail="Video has no completed transcript",
        )

    print(
        f"[Ollama] Starting analysis: "
        f"{video.filename}"
    )

    try:
        result = analyze_transcript(
            video.transcript_segments
        )

        print(
            f"[Ollama] Analysis completed: "
            f"{video.filename}"
        )

        return result

    except Exception as exc:
        print(
            f"[Ollama] Analysis failed: "
            f"{exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Ollama analysis failed: {exc}",
        )


# ============================================================
# CREATE MP4 CLIP
# ============================================================

@app.post(
    "/projects/{project_id}/videos/{video_id}/clips"
)
def create_clip(
    project_id: str,
    video_id: str,
    start: float,
    end: float,
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.project_id == project_id,
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    try:
        start = float(start)
        end = float(end)

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid clip timestamps",
        )

    if start < 0:
        raise HTTPException(
            status_code=400,
            detail="Clip start cannot be negative",
        )

    if end <= start:
        raise HTTPException(
            status_code=400,
            detail="Clip end must be greater than start",
        )

    duration = end - start

    if duration < 1:
        raise HTTPException(
            status_code=400,
            detail="Clip must be at least 1 second long",
        )

    if duration > 120:
        raise HTTPException(
            status_code=400,
            detail="Clip cannot be longer than 120 seconds",
        )

    source_path = Path(video.storage_path)

    if not source_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Source video file not found: "
                f"{source_path}"
            ),
        )

    clips_dir = (
        UPLOAD_DIR
        / project_id
        / "clips"
    )

    clips_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    clip_id = str(uuid4())
    output_filename = f"{clip_id}.mp4"

    output_path = clips_dir / output_filename

    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        str(source_path),
        "-t",
        str(duration),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    print(
        f"[Clip] Creating clip: "
        f"{video.filename} "
        f"{start:.2f}s -> {end:.2f}s"
    )

    print(
        "[Clip] FFmpeg command:",
        " ".join(command),
    )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=(
                "FFmpeg is not installed "
                "inside the backend container."
            ),
        )

    except subprocess.TimeoutExpired:
        if output_path.exists():
            output_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                "FFmpeg timed out while "
                "creating the clip."
            ),
        )

    if result.returncode != 0:
        print("[Clip] FFmpeg failed:")
        print(result.stderr)

        if output_path.exists():
            output_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="FFmpeg failed to create the clip.",
        )

    if not output_path.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "FFmpeg completed but "
                "the output file was not created."
            ),
        )

    file_size = output_path.stat().st_size

    if file_size == 0:
        output_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Generated clip is empty.",
        )

    print(
        f"[Clip] Created successfully: "
        f"{output_path}"
    )

    print(
        f"[Clip] Size: "
        f"{file_size / 1024 / 1024:.2f} MB"
    )

    # --------------------------------------------------------
    # SAVE CLIP METADATA TO DATABASE
    # --------------------------------------------------------

    clip = Clip(
        id=clip_id,
        project_id=project_id,
        video_id=video_id,
        filename=output_filename,
        storage_path=str(output_path),
        start_time=start,
        end_time=end,
        duration=duration,
    )

    try:
        db.add(clip)
        db.commit()
        db.refresh(clip)

    except Exception as e:
        db.rollback()

        if output_path.exists():
            output_path.unlink()

        print(
            f"[Clip] Failed to save database record: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Clip was generated, but "
                "saving it to the database failed."
            ),
        )

    print(
        f"[Clip] Database record saved: {clip.id}"
    )

    return {
        "success": True,
        "clip_id": clip.id,
        "filename": clip.filename,
        "start": clip.start_time,
        "end": clip.end_time,
        "duration": clip.duration,
        "size": file_size,
        "url": (
            f"/projects/"
            f"{project_id}/clips/"
            f"{clip.filename}"
        ),
        "created_at": clip.created_at,
    }


# ============================================================
# SERVE GENERATED MP4 CLIP
# ============================================================

@app.get(
    "/projects/{project_id}/clips/{filename}"
)
def get_clip(
    project_id: str,
    filename: str,
    db: Session = Depends(get_db),
):
    safe_filename = Path(filename).name

    clip = (
        db.query(Clip)
        .filter(
            Clip.project_id == project_id,
            Clip.filename == safe_filename,
        )
        .first()
    )

    if not clip:
        raise HTTPException(
            status_code=404,
            detail="Clip not found in database",
        )

    file_path = Path(clip.storage_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Clip file not found",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Clip file not found",
        )

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=safe_filename,
    )