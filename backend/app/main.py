from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine
from app.models import Base

app = FastAPI(title="ClipForge API")


Base.metadata.create_all(bind=engine)


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