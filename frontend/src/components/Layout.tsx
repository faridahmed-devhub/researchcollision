import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Atom,
  BookOpen,
  FileText,
  FlaskConical,
  GitBranch,
  LayoutDashboard,
  Lightbulb,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../stores/auth";
import { useWorkspaceStore } from "../stores/workspace";
import type { ProviderStatus, Workspace } from "../lib/types";
import { clsx } from "clsx";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/profile", label: "Research Profile", icon: Atom },
  { to: "/literature", label: "Literature", icon: BookOpen },
  { to: "/researchers", label: "Researchers", icon: Users },
  { to: "/discovery", label: "Discovery", icon: FlaskConical },
  { to: "/intersections", label: "Intersections", icon: GitBranch },
  { to: "/gaps", label: "Gaps", icon: ShieldCheck },
  { to: "/hypotheses", label: "Hypotheses", icon: Lightbulb },
  { to: "/collaborations", label: "Collaborations", icon: Users },
  { to: "/paper-draft", label: "Paper Draft", icon: FileText },
  { to: "/evidence", label: "Evidence", icon: ShieldCheck },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const { active, setActive } = useWorkspaceStore();

  const workspacesQ = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: async () => (await api.get("/workspaces")).data,
  });

  const providerQ = useQuery<ProviderStatus>({
    queryKey: ["provider-status"],
    queryFn: async () => (await api.get("/meta/provider-status")).data,
    staleTime: 60_000,
  });

  function handleLogout() {
    logout();
    setActive(null);
    navigate("/login");
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-900 text-slate-300 transition-transform md:static md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-white">
            <Atom size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">ResearchCollision</p>
            <p className="text-[11px] text-slate-400">Intersection Discovery</p>
          </div>
          <button className="ml-auto text-slate-400 md:hidden" onClick={() => setOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-primary-600/20 font-medium text-white"
                    : "hover:bg-slate-800 hover:text-white"
                )
              }
            >
              <Icon size={17} className="shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {providerQ.data?.mock_mode && (
          <div className="mx-3 mb-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] leading-snug text-amber-300">
            Mock mode — deterministic demo providers, no external API calls.
          </div>
        )}

        <div className="border-t border-slate-800 p-4">
          <p className="truncate text-sm font-medium text-white">{user?.name}</p>
          <p className="truncate text-xs text-slate-400">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="mt-2 flex items-center gap-2 text-xs text-slate-400 hover:text-white"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>

      {open && (
        <div className="fixed inset-0 z-20 bg-black/40 md:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 md:px-6">
          <button className="text-slate-500 md:hidden" onClick={() => setOpen(true)}>
            <Menu size={20} />
          </button>
          <select
            aria-label="Active workspace"
            className="input max-w-xs"
            value={active?.id ?? ""}
            onChange={(e) => {
              const ws = workspacesQ.data?.find((w) => w.id === e.target.value);
              setActive(ws ?? null);
            }}
          >
            {(workspacesQ.data ?? []).map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          <div className="ml-auto text-xs text-slate-400">
            {providerQ.data && (
              <span>
                LLM: <b>{providerQ.data.llm_provider}</b> · Literature:{" "}
                <b>{providerQ.data.literature_provider}</b>
              </span>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
