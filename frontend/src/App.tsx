import { useEffect, useRef, useState, type ReactNode } from "react"

import {
  ArrowLeft,
  BarChart3,
  Bell,
  CheckCircle2,
  ChevronDown,
  Clapperboard,
  Clock,
  Folder,
  Home,
  Loader2,
  Plus,
  Settings,
  Trash2,
  Upload,
  Video,
  X,
  Zap,
  AlertCircle,
} from "lucide-react"

const API_URL = "http://localhost:8000"
const DEV_USER_ID = "f43f80ba-f4a2-49f2-8842-c303a4394787"

type Project = {
  id: string
  name: string
  user_id: string
  created_at: string
}

type TranscriptSegment = {
  start: number
  end: number
  text: string
}

type VideoFile = {
  id: string
  project_id: string
  filename: string
  storage_path: string
  processing_status: string
  transcript: string | null
  transcript_segments: TranscriptSegment[] | null
  processing_error: string | null
  created_at: string
}

function App() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)

  const [selectedProject, setSelectedProject] =
    useState<Project | null>(null)

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")

  async function loadProjects() {
    try {
      setLoadingProjects(true)

      const response = await fetch(
        `${API_URL}/projects?user_id=${DEV_USER_ID}`
      )

      if (!response.ok) {
        throw new Error(
          `Failed to load projects: ${response.status}`
        )
      }

      const data: Project[] = await response.json()

      setProjects(data)
    } catch (err) {
      console.error("Failed to load projects:", err)
    } finally {
      setLoadingProjects(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  async function createProject() {
    const name = projectName.trim()

    if (!name) {
      setError("Please enter a project name.")
      return
    }

    setCreating(true)
    setError("")

    try {
      const response = await fetch(`${API_URL}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          user_id: DEV_USER_ID,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()

        throw new Error(
          errorText ||
            `Request failed with status ${response.status}`
        )
      }

      const createdProject: Project = await response.json()

      setProjects((currentProjects) => [
        createdProject,
        ...currentProjects,
      ])

      setProjectName("")
      setShowCreateModal(false)
    } catch (err) {
      console.error("Failed to create project:", err)

      setError(
        err instanceof Error
          ? err.message
          : "Failed to create project."
      )
    } finally {
      setCreating(false)
    }
  }

  async function deleteProject(project: Project) {
    const confirmed = window.confirm(
      `Delete project "${project.name}"?\n\nThis will permanently delete the project, its videos, transcripts and uploaded video files.`
    )

    if (!confirmed) return

    try {
      const response = await fetch(
        `${API_URL}/projects/${project.id}`,
        {
          method: "DELETE",
        }
      )

      if (!response.ok) {
        let message = "Failed to delete project."

        try {
          const data = await response.json()

          if (data.detail) {
            message = data.detail
          }
        } catch {
          // Ignore invalid JSON.
        }

        throw new Error(message)
      }

      setProjects((currentProjects) =>
        currentProjects.filter(
          (item) => item.id !== project.id
        )
      )

      if (selectedProject?.id === project.id) {
        setSelectedProject(null)
      }
    } catch (err) {
      console.error("Failed to delete project:", err)

      window.alert(
        err instanceof Error
          ? err.message
          : "Failed to delete project."
      )
    }
  }

  function openCreateModal() {
    setProjectName("")
    setError("")
    setShowCreateModal(true)
  }

  function closeCreateModal() {
    if (creating) return

    setProjectName("")
    setError("")
    setShowCreateModal(false)
  }

  function openProject(project: Project) {
    setSelectedProject(project)
  }

  function closeProject() {
    setSelectedProject(null)
    loadProjects()
  }

  if (selectedProject) {
    return (
      <ProjectPage
        project={selectedProject}
        onBack={closeProject}
      />
    )
  }

  return (
    <div className="flex min-h-screen bg-[#08090b] text-white">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-white/10 bg-[#0d0f12] md:flex">
        <div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 shadow-lg shadow-orange-500/20">
            <Clapperboard size={20} strokeWidth={2.5} />
          </div>

          <span className="text-xl font-bold tracking-tight">
            Clip<span className="text-orange-400">Forge</span>
          </span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-6">
          <NavItem
            icon={<Home size={19} />}
            label="Dashboard"
            active
          />

          <NavItem
            icon={<Folder size={19} />}
            label="Projects"
          />

          <NavItem
            icon={<Upload size={19} />}
            label="Upload"
          />

          <div className="px-3 pb-2 pt-8 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            Workspace
          </div>

          <NavItem
            icon={<BarChart3 size={19} />}
            label="Analytics"
          />

          <NavItem
            icon={<Settings size={19} />}
            label="Settings"
          />
        </nav>

        <div className="m-3 rounded-2xl border border-orange-500/20 bg-gradient-to-br from-orange-500/10 to-transparent p-4">
          <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-orange-500/10 text-orange-400">
            <Zap size={18} />
          </div>

          <p className="text-sm font-semibold">
            Unlock ClipForge Pro
          </p>

          <p className="mt-1 text-xs leading-5 text-zinc-500">
            Create more clips and unlock advanced AI features.
          </p>

          <button className="mt-4 w-full rounded-xl bg-orange-500 py-2 text-xs font-semibold transition hover:bg-orange-400">
            Upgrade
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="min-w-0 flex-1">
        <header className="flex h-20 items-center justify-between border-b border-white/10 bg-[#0a0b0d]/80 px-5 backdrop-blur-xl md:px-8">
          <div>
            <p className="text-sm text-zinc-500">
              Workspace
            </p>

            <h2 className="text-lg font-semibold">
              Dashboard
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-zinc-400 transition hover:bg-white/[0.07] hover:text-white">
              <Bell size={18} />

              <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-orange-500" />
            </button>

            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-orange-400 to-orange-600 text-xs font-bold">
                M
              </div>

              <span className="hidden text-sm font-medium sm:block">
                My Account
              </span>

              <ChevronDown
                size={15}
                className="text-zinc-500"
              />
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-7xl p-5 md:p-8">
          {/* Hero */}
          <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#15171b] via-[#101216] to-[#0c0d10] p-7 md:p-10">
            <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl" />

            <div className="relative max-w-2xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-orange-500/20 bg-orange-500/10 px-3 py-1.5 text-xs font-medium text-orange-300">
                <Zap size={13} />
                AI-powered video clipping
              </div>

              <h1 className="text-3xl font-bold tracking-tight md:text-5xl">
                Turn long videos into
                <span className="text-orange-400">
                  {" "}
                  viral clips.
                </span>
              </h1>

              <p className="mt-4 max-w-xl text-sm leading-6 text-zinc-400 md:text-base">
                Upload your content and let ClipForge find the best
                moments, create clips, and prepare them for social media.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <button
                  onClick={openCreateModal}
                  className="flex items-center gap-2 rounded-xl bg-orange-500 px-5 py-3 text-sm font-semibold transition hover:bg-orange-400"
                >
                  <Plus size={18} />
                  Create Project
                </button>
              </div>
            </div>
          </section>

          {/* Stats */}
          <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Projects"
              value={String(projects.length)}
            />

            <StatCard
              title="Videos processed"
              value="12"
            />

            <StatCard
              title="Clips generated"
              value="44"
            />

            <StatCard
              title="Processing time"
              value="2.4h"
            />
          </section>

          {/* Quick Upload */}
          <section className="mt-8">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">
                Quick Upload
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Open a project to upload a video
              </p>
            </div>

            <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-8 md:p-12">
              <div className="mx-auto flex max-w-lg flex-col items-center text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-orange-400">
                  <Upload size={25} />
                </div>

                <h3 className="mt-5 text-base font-semibold">
                  Select a project first
                </h3>

                <p className="mt-2 text-sm text-zinc-500">
                  Open one of your projects below to upload a video.
                </p>
              </div>
            </div>
          </section>

          {/* Projects */}
          <section className="mt-10">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Recent Projects
                </h2>

                <p className="mt-1 text-sm text-zinc-500">
                  Continue working on your projects
                </p>
              </div>

              <button className="text-sm font-medium text-orange-400 transition hover:text-orange-300">
                View all
              </button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {loadingProjects ? (
                <div className="col-span-full rounded-2xl border border-white/10 bg-[#101216] p-8 text-center text-sm text-zinc-500">
                  Loading projects...
                </div>
              ) : projects.length === 0 ? (
                <div className="col-span-full rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-8 text-center text-sm text-zinc-500">
                  No projects yet. Create your first project.
                </div>
              ) : (
                projects.map((project) => (
                  <div
                    key={project.id}
                    className="group relative"
                  >
                    <ProjectCard
                      name={project.name}
                      clips={0}
                      updated={new Date(
                        project.created_at
                      ).toLocaleString()}
                      color="from-violet-500/30 to-blue-500/10"
                      onClick={() => openProject(project)}
                    />

                    <button
                      onClick={(event) => {
                        event.stopPropagation()
                        deleteProject(project)
                      }}
                      className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-xl border border-red-500/20 bg-black/50 text-red-400 opacity-0 backdrop-blur transition hover:bg-red-500/20 group-hover:opacity-100"
                      title="Delete project"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </main>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeCreateModal()
            }
          }}
        >
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-[#111318] p-6 shadow-2xl shadow-black/50">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Create Project
                </h2>

                <p className="mt-1 text-sm text-zinc-500">
                  Give your new video project a name.
                </p>
              </div>

              <button
                onClick={closeCreateModal}
                disabled={creating}
                className="flex h-9 w-9 items-center justify-center rounded-xl text-zinc-500 transition hover:bg-white/[0.05] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-6">
              <label className="mb-2 block text-sm font-medium text-zinc-300">
                Project name
              </label>

              <input
                autoFocus
                value={projectName}
                onChange={(event) => {
                  setProjectName(event.target.value)
                  setError("")
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !creating) {
                    createProject()
                  }
                }}
                placeholder="e.g. My YouTube Shorts"
                disabled={creating}
                className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-zinc-600 focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/10 disabled:opacity-50"
              />

              {error && (
                <p className="mt-3 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                  {error}
                </p>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={closeCreateModal}
                disabled={creating}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm font-semibold text-zinc-300 transition hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                onClick={createProject}
                disabled={creating || !projectName.trim()}
                className="rounded-xl bg-orange-500 px-5 py-2.5 text-sm font-semibold transition hover:bg-orange-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {creating ? "Creating..." : "Create Project"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* PROJECT PAGE */

function ProjectPage({
  project,
  onBack,
}: {
  project: Project
  onBack: () => void
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [videos, setVideos] = useState<VideoFile[]>([])
  const [loadingVideos, setLoadingVideos] = useState(true)

  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState("")
  const [uploadSuccess, setUploadSuccess] = useState("")

  const [deletingVideoId, setDeletingVideoId] =
    useState<string | null>(null)

  async function loadVideos(showLoading = false) {
    try {
      // Only show the loading screen during the FIRST load.
      // Background refreshes must not replace the video list.
      if (showLoading) {
        setLoadingVideos(true)
      }

      const response = await fetch(
        `${API_URL}/projects/${project.id}/videos`
      )

      if (!response.ok) {
        throw new Error(
          `Failed to load videos: ${response.status}`
        )
      }

      const data: VideoFile[] = await response.json()

      setVideos((currentVideos) => {
        // Avoid unnecessary React re-renders when nothing changed.
        if (
          JSON.stringify(currentVideos) ===
          JSON.stringify(data)
        ) {
          return currentVideos
        }

        return data
      })
    } catch (err) {
      console.error("Failed to load videos:", err)
    } finally {
      if (showLoading) {
        setLoadingVideos(false)
      }
    }
  }

  useEffect(() => {
    // Initial load: show loading state.
    loadVideos(true)

    // Background polling: DO NOT show loading state.
    const interval = window.setInterval(() => {
      loadVideos(false)
    }, 3000)

    return () => {
      window.clearInterval(interval)
    }
  }, [project.id])

  async function deleteVideo(video: VideoFile) {
    const confirmed = window.confirm(
      `Delete "${video.filename}"?\n\nThis will permanently delete the uploaded video and its transcript.`
    )

    if (!confirmed) return

    setDeletingVideoId(video.id)

    try {
      const response = await fetch(
        `${API_URL}/projects/${project.id}/videos/${video.id}`,
        {
          method: "DELETE",
        }
      )

      if (!response.ok) {
        let message = "Failed to delete video."

        try {
          const data = await response.json()

          if (data.detail) {
            message = data.detail
          }
        } catch {
          // Ignore invalid JSON.
        }

        throw new Error(message)
      }

      setVideos((currentVideos) =>
        currentVideos.filter(
          (item) => item.id !== video.id
        )
      )
    } catch (err) {
      console.error("Failed to delete video:", err)

      window.alert(
        err instanceof Error
          ? err.message
          : "Failed to delete video."
      )
    } finally {
      setDeletingVideoId(null)
    }
  }

  function openFilePicker() {
    if (uploading) return

    setUploadError("")
    setUploadSuccess("")

    fileInputRef.current?.click()
  }

  function uploadFile(file: File) {
    setUploadError("")
    setUploadSuccess("")
    setUploadProgress(0)

    const allowedExtensions = [
      ".mp4",
      ".mov",
      ".avi",
      ".mkv",
      ".webm",
      ".m4v",
    ]

    const filename = file.name.toLowerCase()

    const isAllowed = allowedExtensions.some(
      (extension) => filename.endsWith(extension)
    )

    if (!isAllowed) {
      setUploadError(
        "Unsupported video format. Please select MP4, MOV, AVI, MKV, WebM or M4V."
      )

      return
    }

    const maxSize = 10 * 1024 * 1024 * 1024

    if (file.size > maxSize) {
      setUploadError("The maximum file size is 10 GB.")
      return
    }

    const formData = new FormData()

    formData.append("file", file)

    const xhr = new XMLHttpRequest()

    xhr.open(
      "POST",
      `${API_URL}/projects/${project.id}/videos`
    )

    setUploading(true)

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const progress = Math.round(
          (event.loaded / event.total) * 100
        )

        setUploadProgress(progress)
      }
    }

    xhr.onload = async () => {
      setUploading(false)

      if (xhr.status >= 200 && xhr.status < 300) {
        setUploadProgress(100)

        setUploadSuccess(
          `"${file.name}" uploaded successfully. Whisper transcription has started.`
        )

        if (fileInputRef.current) {
          fileInputRef.current.value = ""
        }

        // Refresh without showing the loading screen.
        await loadVideos(false)
      } else {
        let message = "Video upload failed."

        try {
          const data = JSON.parse(xhr.responseText)

          if (data.detail) {
            message = data.detail
          }
        } catch {
          // Ignore invalid JSON response.
        }

        setUploadError(message)
      }
    }

    xhr.onerror = () => {
      setUploading(false)

      setUploadError(
        "Could not connect to the ClipForge backend."
      )
    }

    xhr.onabort = () => {
      setUploading(false)
      setUploadError("Upload was cancelled.")
    }

    xhr.send(formData)
  }

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0]

    if (!file) return

    uploadFile(file)
  }

  return (
    <div className="min-h-screen bg-[#08090b] text-white">
      {/* Top bar */}
      <header className="flex h-20 items-center justify-between border-b border-white/10 bg-[#0a0b0d]/80 px-5 backdrop-blur-xl md:px-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-white/[0.07] hover:text-white"
        >
          <ArrowLeft size={17} />
          Back to Dashboard
        </button>

        <div className="flex items-center gap-3">
          <button className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-zinc-400 transition hover:bg-white/[0.07] hover:text-white">
            <Bell size={18} />

            <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-orange-500" />
          </button>

          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-orange-400 to-orange-600 text-xs font-bold">
              M
            </div>

            <span className="hidden text-sm font-medium sm:block">
              My Account
            </span>

            <ChevronDown
              size={15}
              className="text-zinc-500"
            />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl p-5 md:p-8">
        {/* Project heading */}
        <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#15171b] via-[#101216] to-[#0c0d10] p-7 md:p-10">
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl" />

          <div className="relative">
            <div className="mb-4 flex items-center gap-2 text-sm text-zinc-500">
              <Folder size={16} />
              Project
            </div>

            <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
              {project.name}
            </h1>

            <p className="mt-3 text-sm text-zinc-500">
              Created{" "}
              {new Date(project.created_at).toLocaleString()}
            </p>
          </div>
        </section>

        {/* Upload */}
        <section className="mt-8">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">
              Upload Video
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Upload a long-form video and ClipForge will prepare it
              for AI clipping.
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".mp4,.mov,.avi,.mkv,.webm,.m4v,video/*"
            onChange={handleFileChange}
            className="hidden"
          />

          <button
            type="button"
            onClick={openFilePicker}
            disabled={uploading}
            className="group w-full cursor-pointer rounded-3xl border border-dashed border-white/15 bg-white/[0.02] p-10 text-left transition hover:border-orange-500/40 hover:bg-orange-500/[0.02] disabled:cursor-not-allowed disabled:opacity-70 md:p-16"
          >
            <div className="mx-auto flex max-w-xl flex-col items-center text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-orange-400 transition group-hover:scale-105 group-hover:bg-orange-500/10">
                <Upload size={28} />
              </div>

              <h3 className="mt-6 text-lg font-semibold">
                {uploading
                  ? "Uploading video..."
                  : "Select your video"}
              </h3>

              <p className="mt-2 text-sm text-zinc-500">
                {uploading
                  ? `${uploadProgress}% uploaded`
                  : "Click anywhere here to browse your computer"}
              </p>

              <p className="mt-4 text-xs text-zinc-600">
                MP4, MOV, AVI, MKV, WebM or M4V · Up to 10 GB
              </p>

              {!uploading && (
                <span className="mt-6 flex items-center gap-2 rounded-xl bg-orange-500 px-5 py-3 text-sm font-semibold transition group-hover:bg-orange-400">
                  <Upload size={17} />
                  Select Video
                </span>
              )}

              {uploading && (
                <div className="mt-6 w-full max-w-md">
                  <div className="h-2 overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-orange-500 transition-all duration-200"
                      style={{
                        width: `${uploadProgress}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </button>

          {uploadSuccess && (
            <div className="mt-4 rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm text-green-400">
              {uploadSuccess}
            </div>
          )}

          {uploadError && (
            <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {uploadError}
            </div>
          )}
        </section>

        {/* Videos */}
        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">
              Videos
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Videos uploaded to this project
            </p>
          </div>

          {loadingVideos ? (
            <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-10 text-center">
              <Loader2
                size={25}
                className="mx-auto animate-spin text-orange-400"
              />

              <p className="mt-4 text-sm text-zinc-500">
                Loading videos...
              </p>
            </div>
          ) : videos.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-10 text-center">
              <Video
                size={30}
                className="mx-auto text-zinc-700"
              />

              <p className="mt-4 text-sm text-zinc-500">
                No videos uploaded yet.
              </p>

              <p className="mt-1 text-xs text-zinc-600">
                Upload your first video to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {videos.map((video) => (
                <VideoCard
                  key={video.id}
                  video={video}
                  deleting={deletingVideoId === video.id}
                  onDelete={() => deleteVideo(video)}
                />
              ))}
            </div>
          )}
        </section>

        {/* Generated Clips */}
        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">
              Generated Clips
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              AI-generated clips will appear here.
            </p>
          </div>

          <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-10 text-center">
            <Clapperboard
              size={30}
              className="mx-auto text-zinc-700"
            />

            <p className="mt-4 text-sm text-zinc-500">
              No clips generated yet.
            </p>

            <p className="mt-1 text-xs text-zinc-600">
              Upload a video and start processing to generate clips.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}

/* VIDEO CARD */

function VideoCard({
  video,
  deleting,
  onDelete,
}: {
  video: VideoFile
  deleting: boolean
  onDelete: () => void
}) {
  const [showTranscript, setShowTranscript] =
    useState(false)

  function formatTime(seconds: number) {
    const totalSeconds = Math.floor(seconds)

    const minutes = Math.floor(totalSeconds / 60)
    const remainingSeconds = totalSeconds % 60

    return `${String(minutes).padStart(2, "0")}:${String(
      remainingSeconds
    ).padStart(2, "0")}`
  }

  function getStatus() {
    switch (video.processing_status) {
      case "completed":
        return {
          label: "Transcription complete",
          icon: <CheckCircle2 size={15} />,
          className:
            "border-green-500/20 bg-green-500/10 text-green-400",
        }

      case "processing":
        return {
          label: "Transcribing...",
          icon: (
            <Loader2
              size={15}
              className="animate-spin"
            />
          ),
          className:
            "border-orange-500/20 bg-orange-500/10 text-orange-400",
        }

      case "failed":
        return {
          label: "Processing failed",
          icon: <AlertCircle size={15} />,
          className:
            "border-red-500/20 bg-red-500/10 text-red-400",
        }

      default:
        return {
          label: "Waiting for processing",
          icon: <Clock size={15} />,
          className:
            "border-yellow-500/20 bg-yellow-500/10 text-yellow-400",
        }
    }
  }

  const status = getStatus()

  return (
    <div className="rounded-2xl border border-white/10 bg-[#101216] p-5 transition hover:border-orange-500/30">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-orange-500/10 text-orange-400">
          <Video size={21} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <h3 className="truncate font-semibold">
                {video.filename}
              </h3>

              <p className="mt-1 text-xs text-zinc-600">
                Uploaded{" "}
                {new Date(
                  video.created_at
                ).toLocaleString()}
              </p>
            </div>

            <button
              onClick={onDelete}
              disabled={deleting}
              className="flex shrink-0 items-center justify-center gap-2 rounded-xl border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs font-semibold text-red-400 transition hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {deleting ? (
                <Loader2
                  size={14}
                  className="animate-spin"
                />
              ) : (
                <Trash2 size={14} />
              )}

              {deleting ? "Deleting..." : "Delete"}
            </button>
          </div>

          {/* Status */}
          <div className="mt-4">
            <span
              className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium ${status.className}`}
            >
              {status.icon}
              {status.label}
            </span>
          </div>
        </div>
      </div>

      {/* Processing error */}
      {video.processing_status === "failed" &&
        video.processing_error && (
          <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
            <div className="flex gap-3">
              <AlertCircle
                size={17}
                className="mt-0.5 shrink-0 text-red-400"
              />

              <div>
                <p className="text-sm font-medium text-red-400">
                  Whisper processing failed
                </p>

                <p className="mt-1 break-words text-xs leading-5 text-red-400/70">
                  {video.processing_error}
                </p>
              </div>
            </div>
          </div>
        )}

      {/* Processing */}
      {video.processing_status === "processing" && (
        <div className="mt-4 rounded-xl border border-orange-500/10 bg-orange-500/5 p-4">
          <div className="flex items-center gap-3">
            <Loader2
              size={18}
              className="animate-spin text-orange-400"
            />

            <div>
              <p className="text-sm font-medium text-orange-300">
                AI transcription in progress
              </p>

              <p className="mt-1 text-xs text-orange-400/60">
                Whisper is analyzing the audio and generating
                timestamped segments.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Transcript */}
      {video.processing_status === "completed" &&
        video.transcript && (
          <div className="mt-4 overflow-hidden rounded-xl border border-white/10 bg-black/20">
            <button
              onClick={() =>
                setShowTranscript(
                  (current) => !current
                )
              }
              className="flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-white/[0.03]"
            >
              <div>
                <p className="text-sm font-semibold">
                  Transcript
                </p>

                <p className="mt-1 text-xs text-zinc-600">
                  {video.transcript_segments?.length ?? 0}{" "}
                  timestamped segments
                </p>
              </div>

              <ChevronDown
                size={17}
                className={`text-zinc-500 transition-transform ${
                  showTranscript
                    ? "rotate-180"
                    : ""
                }`}
              />
            </button>

            {showTranscript && (
              <div className="border-t border-white/10">
                {/* Full transcript */}
                <div className="p-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-600">
                    Full transcript
                  </p>

                  <p className="text-sm leading-6 text-zinc-300">
                    {video.transcript}
                  </p>
                </div>

                {/* Timestamped segments */}
                {video.transcript_segments &&
                  video.transcript_segments.length > 0 && (
                    <div className="border-t border-white/10">
                      <div className="p-4">
                        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-600">
                          Timestamped transcript
                        </p>

                        <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
                          {video.transcript_segments.map(
                            (segment, index) => (
                              <div
                                key={`${video.id}-${index}`}
                                className="group flex gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition hover:border-orange-500/20 hover:bg-orange-500/[0.02]"
                              >
                                <div className="shrink-0">
                                  <span className="inline-flex items-center rounded-lg bg-orange-500/10 px-2 py-1 font-mono text-xs font-medium text-orange-400">
                                    {formatTime(
                                      segment.start
                                    )}
                                  </span>
                                </div>

                                <p className="text-sm leading-6 text-zinc-300">
                                  {segment.text}
                                </p>

                                <span className="ml-auto hidden shrink-0 self-center font-mono text-[10px] text-zinc-700 group-hover:block">
                                  {formatTime(
                                    segment.end
                                  )}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    </div>
                  )}
              </div>
            )}
          </div>
        )}
    </div>
  )
}

/* NAV ITEM */

function NavItem({
  icon,
  label,
  active = false,
}: {
  icon: ReactNode
  label: string
  active?: boolean
}) {
  return (
    <button
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
        active
          ? "bg-orange-500/10 text-orange-400"
          : "text-zinc-500 hover:bg-white/[0.04] hover:text-white"
      }`}
    >
      {icon}
      {label}
    </button>
  )
}

/* STAT CARD */

function StatCard({
  title,
  value,
}: {
  title: string
  value: string
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#101216] p-5">
      <p className="text-sm text-zinc-500">
        {title}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {value}
      </p>
    </div>
  )
}

/* PROJECT CARD */

function ProjectCard({
  name,
  clips,
  updated,
  color,
  onClick,
}: {
  name: string
  clips: number
  updated: string
  color: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="group w-full overflow-hidden rounded-2xl border border-white/10 bg-[#101216] text-left transition hover:-translate-y-0.5 hover:border-orange-500/40 hover:shadow-lg hover:shadow-orange-500/5"
    >
      <div
        className={`relative flex h-36 items-center justify-center bg-gradient-to-br ${color}`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-black/20 text-white backdrop-blur transition group-hover:scale-110">
          <Video size={22} />
        </div>

        <div className="absolute bottom-3 left-3 rounded-lg bg-black/40 px-2.5 py-1 text-xs text-zinc-300 backdrop-blur">
          {clips} clips
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-semibold">
          {name}
        </h3>

        <p className="mt-1 text-xs text-zinc-600">
          Updated {updated}
        </p>
      </div>
    </button>
  )
}

export default App