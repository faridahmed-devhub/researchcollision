import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import { BookOpen, GitBranch, Lightbulb, ShieldCheck, Users, FlaskConical } from "lucide-react";
import { api } from "../lib/api";
import type { DiscoveryJob, Intersection, Workspace, WorkspaceStats } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, PageSpinner, StatCard } from "../components/ui";

export default function DashboardPage() {
  const { active, setActive } = useWorkspaceStore();

  const workspacesQ = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: async () => (await api.get("/workspaces")).data,
  });

  useEffect(() => {
    if (!active && workspacesQ.data && workspacesQ.data.length > 0) {
      setActive(workspacesQ.data[0]);
    }
  }, [active, workspacesQ.data, setActive]);

  const wid = active?.id;

  const statsQ = useQuery<WorkspaceStats>({
    queryKey: ["stats", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/stats`)).data,
    enabled: !!wid,
  });

  const intersectionsQ = useQuery<Intersection[]>({
    queryKey: ["intersections", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/intersections`)).data,
    enabled: !!wid,
  });

  const jobsQ = useQuery<DiscoveryJob[]>({
    queryKey: ["jobs", wid],
    queryFn: async () => (await api.get(`/discovery/workspaces/${wid}/jobs`)).data,
    enabled: !!wid,
    refetchInterval: (q) =>
      q.state.data?.some((j) => j.status === "RUNNING" || j.status === "PENDING") ? 2000 : false,
  });

  if (!wid) {
    return (
      <EmptyState
        title="No workspace yet"
        hint="Create a workspace in Settings to start discovering research intersections."
      />
    );
  }

  const s = statsQ.data;
  const runningJobs = (jobsQ.data ?? []).filter(
    (j) => j.status === "RUNNING" || j.status === "PENDING"
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Dashboard</h1>
          <p className="text-sm text-slate-500">{active?.name}</p>
        </div>
        <Link to="/discovery" className="btn-primary">
          <FlaskConical size={16} /> New discovery
        </Link>
      </div>

      {runningJobs.length > 0 && (
        <div className="card border-primary-200 bg-primary-50 p-4">
          {runningJobs.map((j) => (
            <div key={j.id} className="flex items-center gap-3 text-sm">
              <Badge status={j.status}>{j.status}</Badge>
              <span className="text-slate-600">{j.current_step ?? "queued"}…</span>
              <div className="h-2 w-40 overflow-hidden rounded-full bg-white">
                <div
                  className="h-full rounded-full bg-primary-500 transition-all"
                  style={{ width: `${Math.round(j.progress * 100)}%` }}
                />
              </div>
              <span className="text-xs text-slate-500">
                {Math.round(j.progress * 100)}%
              </span>
            </div>
          ))}
        </div>
      )}

      {statsQ.isLoading ? (
        <PageSpinner />
      ) : s ? (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard icon={<BookOpen size={20} />} label="papers" value={s.papers_analyzed} />
            <StatCard icon={<Users size={20} />} label="researchers" value={s.researchers_analyzed} />
            <StatCard icon={<GitBranch size={20} />} label="intersections" value={s.intersections} />
            <StatCard icon={<ShieldCheck size={20} />} label="gaps" value={s.gaps} />
            <StatCard icon={<Lightbulb size={20} />} label="hypotheses" value={s.hypotheses} />
            <StatCard
              icon={<Users size={20} />}
              label="collaborations"
              value={s.collaboration_opportunities}
            />
            <StatCard
              icon={<ShieldCheck size={20} />}
              label="avg confidence"
              value={`${Math.round(s.avg_confidence * 100)}%`}
            />
            <StatCard icon={<FlaskConical size={20} />} label="active jobs" value={s.active_jobs} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="card p-5">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">Opportunity scores</h2>
              {s.opportunity_scores.length === 0 ? (
                <p className="text-sm text-slate-400">Run a discovery job to see results.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={s.opportunity_scores}>
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-15} height={50} />
                    <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">Publications by year</h2>
              {s.timeline.length === 0 ? (
                <p className="text-sm text-slate-400">No literature collected yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={s.timeline}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">Top topics</h2>
              <div className="flex flex-wrap gap-2">
                {s.topics.map((t) => (
                  <span
                    key={t.name}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600"
                  >
                    {t.name} · {t.count}
                  </span>
                ))}
                {s.topics.length === 0 && (
                  <p className="text-sm text-slate-400">No topics extracted yet.</p>
                )}
              </div>
            </div>

            <div className="card p-5">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">Recent intersections</h2>
              <ul className="space-y-3">
                {(intersectionsQ.data ?? []).slice(0, 4).map((ix) => (
                  <li key={ix.id}>
                    <Link
                      to={`/intersections/${ix.id}`}
                      className="block rounded-lg border border-slate-200 p-3 hover:border-primary-300 hover:bg-primary-50/40"
                    >
                      <p className="line-clamp-1 text-sm font-medium text-slate-800">{ix.title}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        novelty {Math.round(ix.novelty_confidence * 100)}% · feasibility{" "}
                        {Math.round(ix.feasibility_confidence * 100)}% · {ix.discovery_mode}
                      </p>
                    </Link>
                  </li>
                ))}
                {(intersectionsQ.data ?? []).length === 0 && (
                  <li className="text-sm text-slate-400">No intersections yet.</li>
                )}
              </ul>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
