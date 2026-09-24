from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Project, User

app = FastAPI(title="ClipForge API")


class ProjectCreate(BaseModel):
    name: str
    user_id: str


@app.get("/")
def root():
    return {
        "name": "ClipForge",
        "status": "online"
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@app.post("/projects")
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == project_data.user_id
    ).first()

    if not user:
        return {
            "error": "User not found"
        }

    project = Project(
        user_id=user.id,
        name=project_data.name
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "user_id": project.user_id,
        "created_at": project.created_at
    }