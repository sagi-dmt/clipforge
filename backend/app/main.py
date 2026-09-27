from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, get_db
from app.models import Project, User, Video
from app.whisper_service import transcribe_video
from app.ollama_service import analyze_transcript


app = FastAPI(title="ClipForge API")


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


UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ProjectCreate(BaseModel):
    name: str
    user_id: str


@app.get("/")
def root():
    return {
        "name": "ClipForge",
        "status": "online",
    }


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
        if video_path.exists():
            video_path.unlink()

        db.delete(video)
        db.commit()

        return {
            "success": True,
            "message": "Video deleted successfully",
            "video_id": video_id,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Video deletion failed: {str(e)}",
        )


def process_video(video_id: str):
    db = SessionLocal()

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )

        if not video:
            print(f"[Whisper] Video not found: {video_id}")
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
        print(f"[Whisper] Error: {e}")

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
                f"[Whisper] Failed to save error: "
                f"{db_error}"
            )

    finally:
        db.close()


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


@app.post("/projects/{project_id}/videos/{video_id}/analyze")
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