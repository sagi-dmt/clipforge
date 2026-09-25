# ClipForge

ClipForge is a local AI video clipping platform. The goal is to turn long-form videos into short, engaging clips using AI-assisted processing.

## Current Status

The project currently has:

* React + Vite frontend
* Tailwind CSS
* Lucide React icons
* FastAPI backend
* PostgreSQL database
* SQLAlchemy models
* Alembic database migrations
* Docker Compose setup
* Project creation API
* Dark ClipForge dashboard UI

### Currently working

Frontend:

```text
http://localhost:5173/
```

Backend:

```text
http://localhost:8000/
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

The API currently has:

```text
GET  /
GET  /health
POST /projects
```

---

# Project Structure

```text
clipforge/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── index.css
│   │
│   ├── vite.config.ts
│   ├── package.json
│   └── ...
│
├── docker-compose.yml
└── README.md
```

---

# After Restarting the Computer

## 1. Start Docker Desktop

Open Docker Desktop and wait until Docker is running.

## 2. Open PowerShell

Go to the project:

```powershell
cd C:\GitHub\clipforge
```

## 3. Start the backend and PostgreSQL

```powershell
docker compose up -d
```

Check that everything is running:

```powershell
docker compose ps
```

You should see at least:

```text
backend
postgres
```

with a running/up status.

---

# Start the Frontend

Open a second PowerShell window.

Run:

```powershell
cd C:\GitHub\clipforge\frontend
npm run dev
```

Vite should show:

```text
Local: http://localhost:5173/
```

Open:

```text
http://localhost:5173/
```

---

# Check the Backend

Open:

```text
http://localhost:8000/
```

Expected response:

```json
{
  "name": "ClipForge",
  "status": "online"
}
```

Health check:

```text
http://localhost:8000/health
```

Expected:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

API documentation:

```text
http://localhost:8000/docs
```

Currently available:

```text
GET  /
GET  /health
POST /projects
```

---

# Database

PostgreSQL runs inside Docker.

Database:

```text
clipforge
```

Username:

```text
clipforge
```

Password:

```text
clipforge_dev_password
```

Port:

```text
5432
```

Host from Windows:

```text
127.0.0.1
```

HeidiSQL connection:

```text
Network type: PostgreSQL (TCP/IP)
Host: 127.0.0.1
Port: 5432
User: clipforge
Password: clipforge_dev_password
Database: clipforge
```

---

# Database Tables

The current database schema contains:

```text
users
projects
videos
jobs
alembic_version
```

The current SQLAlchemy models are:

```text
User
Project
Video
Job
```

---

# Alembic

Alembic is already configured.

Current migration:

```text
ca198b0181eb_initial_database_schema
```

The migration is currently at:

```text
head
```

Check:

```powershell
docker compose exec backend alembic current
```

Expected:

```text
ca198b0181eb (head)
```

Check for schema changes:

```powershell
docker compose exec backend alembic check
```

Expected:

```text
No new upgrade operations detected.
```

---

# Creating a New Migration

If the SQLAlchemy models are changed:

```powershell
docker compose exec backend alembic revision --autogenerate -m "Describe the change"
```

Then apply it:

```powershell
docker compose exec backend alembic upgrade head
```

---

# Frontend

The frontend uses:

* React
* TypeScript
* Vite
* Tailwind CSS
* Lucide React

Install dependencies if needed:

```powershell
cd C:\GitHub\clipforge\frontend
npm install
```

Start development server:

```powershell
npm run dev
```

Build:

```powershell
npm run build
```

Lint:

```powershell
npm run lint
```

---

# Backend

Backend dependencies are installed inside the Docker image.

Backend technologies:

* FastAPI
* SQLAlchemy
* PostgreSQL
* Psycopg
* Alembic
* Uvicorn

Restart backend:

```powershell
docker compose restart backend
```

View backend logs:

```powershell
docker compose logs backend
```

Follow backend logs:

```powershell
docker compose logs -f backend
```

---

# Project API

## Create Project

Endpoint:

```text
POST /projects
```

Example request:

```json
{
  "name": "My First Project",
  "user_id": "USER_ID_HERE"
}
```

The project is saved into PostgreSQL.

The endpoint currently requires an existing user.

---

# GitHub

Repository:

```text
sagi-dmt/clipforge
```

Before making major changes, commit your work.

Example commit:

```text
Add project creation API
```

Then push to GitHub.

---

# Current Development Position

The project is currently at:

```text
Frontend dashboard
        ↓
FastAPI
        ↓
PostgreSQL
```

The `POST /projects` API is working.

## Next task

The next development step is:

### Connect the frontend "Create Project" button to the backend.

The intended flow is:

```text
Click "Create Project"
        ↓
Project dialog/form
        ↓
POST /projects
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Project appears in dashboard
```

After that:

1. Load projects from PostgreSQL into the frontend
2. Build the Projects page
3. Implement video upload
4. Add Redis
5. Add Celery workers
6. Add FFmpeg processing
7. Add AI transcription
8. Generate clips
9. Add clip preview/export
10. Build the complete ClipForge workflow

---

# Quick Start

After every computer restart:

### Terminal 1

```powershell
cd C:\GitHub\clipforge
docker compose up -d
```

### Terminal 2

```powershell
cd C:\GitHub\clipforge\frontend
npm run dev
```

Then open:

```text
http://localhost:5173/
```

Backend:

```text
http://localhost:8000/
```

API:

```text
http://localhost:8000/docs
```

---

# Useful Docker Commands

Stop containers:

```powershell
docker compose down
```

Start containe
