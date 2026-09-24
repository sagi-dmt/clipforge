import {
  BarChart3,
  Bell,
  ChevronDown,
  Clapperboard,
  Folder,
  Home,
  Plus,
  Settings,
  Upload,
  Video,
  Zap,
} from "lucide-react"

const projects = [
  {
    name: "YouTube Shorts",
    clips: 12,
    updated: "2 hours ago",
    color: "from-violet-500/30 to-blue-500/10",
  },
  {
    name: "Podcast Clips",
    clips: 8,
    updated: "Yesterday",
    color: "from-orange-500/30 to-red-500/10",
  },
  {
    name: "Gaming Highlights",
    clips: 24,
    updated: "3 days ago",
    color: "from-emerald-500/30 to-teal-500/10",
  },
]

function App() {
  return (
    <div className="flex min-h-screen bg-[#08090b] text-white">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-white/10 bg-[#0d0f12] md:flex">
        {/* Logo */}
        <div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 shadow-lg shadow-orange-500/20">
            <Clapperboard size={20} strokeWidth={2.5} />
          </div>

          <span className="text-xl font-bold tracking-tight">
            Clip<span className="text-orange-400">Forge</span>
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-6">
          <NavItem icon={<Home size={19} />} label="Dashboard" active />
          <NavItem icon={<Folder size={19} />} label="Projects" />
          <NavItem icon={<Upload size={19} />} label="Upload" />

          <div className="px-3 pb-2 pt-8 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            Workspace
          </div>

          <NavItem icon={<BarChart3 size={19} />} label="Analytics" />
          <NavItem icon={<Settings size={19} />} label="Settings" />
        </nav>

        {/* Bottom upgrade card */}
        <div className="m-3 rounded-2xl border border-orange-500/20 bg-gradient-to-br from-orange-500/10 to-transparent p-4">
          <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-orange-500/10 text-orange-400">
            <Zap size={18} />
          </div>

          <p className="text-sm font-semibold">Unlock ClipForge Pro</p>

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
        {/* Top bar */}
        <header className="flex h-20 items-center justify-between border-b border-white/10 bg-[#0a0b0d]/80 px-5 backdrop-blur-xl md:px-8">
          <div>
            <p className="text-sm text-zinc-500">Workspace</p>
            <h2 className="text-lg font-semibold">Dashboard</h2>
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

              <ChevronDown size={15} className="text-zinc-500" />
            </div>
          </div>
        </header>

        {/* Dashboard content */}
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
                <span className="text-orange-400"> viral clips.</span>
              </h1>

              <p className="mt-4 max-w-xl text-sm leading-6 text-zinc-400 md:text-base">
                Upload your content and let ClipForge find the best moments,
                create clips, and prepare them for social media.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <button className="flex items-center gap-2 rounded-xl bg-orange-500 px-5 py-3 text-sm font-semibold transition hover:bg-orange-400">
                  <Plus size={18} />
                  Create Project
                </button>

                <button className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-semibold text-zinc-200 transition hover:bg-white/[0.08]">
                  <Upload size={18} />
                  Upload Video
                </button>
              </div>
            </div>
          </section>

          {/* Stats */}
          <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Projects" value="3" />
            <StatCard title="Videos processed" value="12" />
            <StatCard title="Clips generated" value="44" />
            <StatCard title="Processing time" value="2.4h" />
          </section>

          {/* Upload */}
          <section className="mt-8">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Quick Upload</h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Start a new video project
                </p>
              </div>
            </div>

            <div className="group cursor-pointer rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-8 transition hover:border-orange-500/40 hover:bg-orange-500/[0.02] md:p-12">
              <div className="mx-auto flex max-w-lg flex-col items-center text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-orange-400 transition group-hover:scale-105 group-hover:bg-orange-500/10">
                  <Upload size={25} />
                </div>

                <h3 className="mt-5 text-base font-semibold">
                  Drop your video here
                </h3>

                <p className="mt-2 text-sm text-zinc-500">
                  or click to browse your computer
                </p>

                <p className="mt-4 text-xs text-zinc-600">
                  MP4, MOV, MKV or WebM · Up to 10 GB
                </p>
              </div>
            </div>
          </section>

          {/* Projects */}
          <section className="mt-10">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Recent Projects</h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Continue working on your projects
                </p>
              </div>

              <button className="text-sm font-medium text-orange-400 transition hover:text-orange-300">
                View all
              </button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {projects.map((project) => (
                <ProjectCard key={project.name} {...project} />
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

function NavItem({
  icon,
  label,
  active = false,
}: {
  icon: React.ReactNode
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

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#101216] p-5">
      <p className="text-sm text-zinc-500">{title}</p>
      <p className="mt-2 text-2xl font-bold">{value}</p>
    </div>
  )
}

function ProjectCard({
  name,
  clips,
  updated,
  color,
}: {
  name: string
  clips: number
  updated: string
  color: string
}) {
  return (
    <div className="group overflow-hidden rounded-2xl border border-white/10 bg-[#101216] transition hover:-translate-y-0.5 hover:border-white/20">
      <div
        className={`relative h-36 bg-gradient-to-br ${color} flex items-center justify-center`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-black/20 text-white backdrop-blur">
          <Video size={22} />
        </div>

        <div className="absolute bottom-3 left-3 rounded-lg bg-black/40 px-2.5 py-1 text-xs text-zinc-300 backdrop-blur">
          {clips} clips
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-semibold">{name}</h3>
        <p className="mt-1 text-xs text-zinc-600">Updated {updated}</p>
      </div>
    </div>
  )
}

export default App