import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FlaskConical, Pause, Play, RotateCcw, Square, XCircle } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { DiscoveryJob, JobEvent, Researcher } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, ErrorState } from "../components/ui";

export default function DiscoveryPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;
  const qc = useQueryClient();

  const [raQuery, setRaQuery] = useState("");
  const [rbQuery, setRbQuery] = useState("");
  const [ra, setRa] = useState<Researcher | null>(null);
  const [rb, setRb] = useState<Researcher | null>(null);
  const [mode, setMode] = useState("normal");
  const [fieldQuery, setFieldQuery] = useState("");
  const [maxPapers, setMaxPapers] = useState(12);
  const [genHyp, setGenHyp] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const [eventsJobId, setEventsJobId] = useState<string | null>(null);

  const raSearch = useQuery<Researcher[]>({
    queryKey: ["researcher-search", wid, raQuery],
    queryFn: async () =>
      (await api.get(`/researchers/search?q=${encodeURIComponent(raQuery)}&workspace_id=${wid}`)).data,
    enabled: !!wid && raQuery.length >= 2,
  });

  const rbSearch = useQuery<Researcher[]>({
    queryKey: ["researcher-search", wid, rbQuery],
    queryFn: async () =>
      (await api.get(`/researchers/search?q=${encodeURIComponent(rbQuery)}&workspace_id=${wid}`)).data,
    enabled: !!wid && rbQuery.length >= 2,
  });

  const jobsQ = useQuery<DiscoveryJob[]>({
    queryKey: ["jobs", wid],
    queryFn: async () => (await api.get(`/discovery/workspaces/${wid}/jobs`)).data,
    enabled: !!wid,
    refetchInterval: (q) =>
      q.state.data?.some((j) => j.status === "RUNNING" || j.status === "PENDING") ? 2000 : false,
  });

  const eventsQ = useQuery<JobEvent[]>({
    queryKey: ["job-events", eventsJobId],
    queryFn: async () => (await api.get(`/discovery/jobs/${eventsJobId}/events`)).data,
    enabled: !!eventsJobId,
    refetchInterval: (q) => {
      const job = jobsQ.data?.find((j) => j.id === eventsJobId);
      return job && (job.status === "RUNNING" || job.status === "PENDING") ? 2000 : false;
    },
  });

  const createQ = useMutation({
    mutationFn: async () =>
      (
        await api.post<DiscoveryJob>("/discovery/jobs", {
          workspace_id: wid,
          researcher_a_id: ra!.id,
          researcher_b_id: rb?.id ?? null,
          field_query: rb ? undefined : fieldQuery.trim() || null,
          mode,
          max_papers: maxPapers,
          generate_hypotheses: genHyp,
        })
      ).data,
    onSuccess: () => {
      setFormError(null);
      qc.invalidateQueries({ queryKey: ["jobs", wid] });
    },
    onError: (err) => setFormError(apiError(err)),
  });

  const control = useMutation({
    mutationFn: async ({ id, action }: { id: string; action: string }) =>
      (await api.post(`/discovery/jobs/${id}/${action}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs", wid] }),
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!ra) {
      setFormError("Select researcher A first.");
      return;
    }
    if (!rb && !fieldQuery.trim()) {
      setFormError("Pick researcher B or enter a field query.");
      return;
    }
    createQ.mutate();
  }

  if (!wid) return <EmptyState title="Select a workspace first" />;

  const jobs = jobsQ.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Discovery</h1>
        <p className="text-sm text-slate-500">
          Run the 10-step pipeline: literature → analysis → trajectories → gaps → intersections →
          evidence verification → hypotheses → paper draft → ranking.
        </p>
      </div>

      <form onSubmit={submit} className="card space-y-4 p-5" data-testid="new-discovery">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <FlaskConical size={15} /> New discovery run
        </h2>
        {formError && <ErrorState message={formError} />}

        <div className="grid gap-4 md:grid-cols-2">
          <ResearcherPicker
            label="Researcher A"
            value={ra}
            query={raQuery}
            onQuery={setRaQuery}
            results={raSearch.data ?? []}
            onPick={(r) => {
              setRa(r);
              setRaQuery(r.name);
            }}
          />
          <ResearcherPicker
            label="Researcher B (optional — auto-pair if empty)"
            value={rb}
            query={rbQuery}
            onQuery={setRbQuery}
            results={rbSearch.data ?? []}
            onPick={(r) => {
              setRb(r);
              setRbQuery(r.name);
            }}
            onClear={() => {
              setRb(null);
              setRbQuery("");
            }}
          />
        </div>

        <div>
          <label className="label" htmlFor="field-query">
            Field query (virtual researcher){" "}
            <span className="text-xs font-normal text-slate-400">
              — used when no researcher B is selected
            </span>
          </label>
          <input
            id="field-query"
            className="input"
            placeholder="e.g. climate science"
            value={fieldQuery}
            disabled={!!rb}
            onChange={(e) => setFieldQuery(e.target.value)}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="label">Discovery mode</label>
            <select className="input" value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="normal">Normal</option>
              <option value="serendipity">Serendipity</option>
            </select>
          </div>
          <div>
            <label className="label">Max papers per researcher: {maxPapers}</label>
            <input
              type="range"
              min={1}
              max={50}
              value={maxPapers}
              onChange={(e) => setMaxPapers(Number(e.target.value))}
              className="w-full accent-primary-600"
            />
          </div>
          <div className="flex items-end pb-1">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={genHyp}
                onChange={(e) => setGenHyp(e.target.checked)}
                className="h-4 w-4 accent-primary-600"
              />
              Generate hypotheses
            </label>
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={createQ.isPending || !ra}
          data-testid="start-discovery"
        >
          {createQ.isPending ? "Starting…" : "Start discovery"}
        </button>
      </form>

      <div className="space-y-3" data-testid="jobs-list">
        <h2 className="text-sm font-semibold text-slate-700">Jobs</h2>
        {jobs.length === 0 && !jobsQ.isFetching && (
          <EmptyState title="No discovery runs yet" hint="Start your first run above." />
        )}
        {jobs.map((j) => (
          <JobRow
            key={j.id}
            job={j}
            onControl={(action) => control.mutate({ id: j.id, action })}
            busy={control.isPending}
            onEvents={() => setEventsJobId(eventsJobId === j.id ? null : j.id)}
            eventsOpen={eventsJobId === j.id}
          />
        ))}
      </div>

      {eventsJobId && (
        <div className="card p-5">
          <h3 className="mb-3 flex items-center justify-between text-sm font-semibold text-slate-700">
            Job event log
            <button onClick={() => setEventsJobId(null)} className="text-slate-400 hover:text-slate-600">
              <XCircle size={16} />
            </button>
          </h3>
          <ul className="max-h-72 space-y-1.5 overflow-y-auto font-mono text-xs text-slate-600">
            {(eventsQ.data ?? []).map((ev) => (
              <li key={ev.id} className="rounded bg-slate-50 px-2 py-1">
                <span className="text-slate-400">
                  {new Date(ev.created_at).toLocaleTimeString()}{" "}
                </span>
                <span className="font-semibold text-primary-700">{ev.event_type}</span>{" "}
                {ev.message ?? ""}
              </li>
            ))}
            {(eventsQ.data ?? []).length === 0 && <li>No events yet.</li>}
          </ul>
        </div>
      )}
    </div>
  );
}

function ResearcherPicker({
  label,
  value,
  query,
  onQuery,
  results,
  onPick,
  onClear,
}: {
  label: string;
  value: Researcher | null;
  query: string;
  onQuery: (q: string) => void;
  results: Researcher[];
  onPick: (r: Researcher) => void;
  onClear?: () => void;
}) {
  const [focused, setFocused] = useState(false);
  const showResults = focused && query.length >= 2 && results.length > 0 && value?.name !== query;
  return (
    <div className="relative">
      <label className="label">{label}</label>
      <input
        className="input"
        placeholder="Type to search…"
        value={query}
        onFocus={() => setFocused(true)}
        onBlur={() => setTimeout(() => setFocused(false), 150)}
        onChange={(e) => onQuery(e.target.value)}
      />
      {value && onClear && (
        <button
          type="button"
          onClick={onClear}
          className="absolute right-2 top-[34px] text-xs text-slate-400 hover:text-slate-600"
        >
          clear
        </button>
      )}
      {showResults && (
        <ul className="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg">
          {results.map((r) => (
            <li key={r.id}>
              <button
                type="button"
                className="block w-full px-3 py-2 text-left text-sm hover:bg-primary-50"
                onMouseDown={() => onPick(r)}
              >
                <span className="font-medium text-slate-800">{r.name}</span>
                {r.affiliation && <span className="ml-2 text-xs text-slate-400">{r.affiliation}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const STEP_LABELS: Record<string, string> = {
  resolve_inputs: "Resolving inputs",
  literature_search: "Searching literature",
  analyze_papers: "Analyzing papers",
  analyze_trajectories: "Analyzing trajectories",
  detect_gaps: "Detecting gaps",
  discover_intersections: "Discovering intersections",
  verify_evidence: "Verifying evidence",
  generate_hypotheses: "Generating hypotheses",
  write_paper_draft: "Writing paper draft",
  rank_collaborations: "Ranking collaborations",
};

function JobRow({
  job,
  onControl,
  busy,
  onEvents,
  eventsOpen,
}: {
  job: DiscoveryJob;
  onControl: (action: string) => void;
  busy: boolean;
  onEvents: () => void;
  eventsOpen: boolean;
}) {
  const pct = Math.round(job.progress * 100);
  const stepLabel = job.current_step ? STEP_LABELS[job.current_step] ?? job.current_step : "";
  return (
    <div className="card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge status={job.status}>{job.status}</Badge>
        <span className="text-xs text-slate-500">
          attempt {job.attempt} · {new Date(job.created_at).toLocaleString()}
        </span>
        <span className="ml-auto flex gap-1.5">
          {job.status === "RUNNING" && (
            <button className="btn-secondary !px-2 !py-1" disabled={busy} onClick={() => onControl("pause")}>
              <Pause size={13} /> Pause
            </button>
          )}
          {job.status === "PAUSED" && (
            <button className="btn-secondary !px-2 !py-1" disabled={busy} onClick={() => onControl("resume")}>
              <Play size={13} /> Resume
            </button>
          )}
          {["PENDING", "RUNNING", "PAUSED"].includes(job.status) && (
            <button className="btn-danger !px-2 !py-1" disabled={busy} onClick={() => onControl("cancel")}>
              <Square size={13} /> Cancel
            </button>
          )}
          {["FAILED", "CANCELLED"].includes(job.status) && (
            <button className="btn-secondary !px-2 !py-1" disabled={busy} onClick={() => onControl("retry")}>
              <RotateCcw size={13} /> Retry
            </button>
          )}
          <button className="btn-secondary !px-2 !py-1" onClick={onEvents}>
            {eventsOpen ? "Hide log" : "Log"}
          </button>
        </span>
      </div>

      <div className="mt-3 flex items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
          <div
            className={`h-full rounded-full transition-all ${
              job.status === "FAILED" ? "bg-red-400" : "bg-primary-500"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="w-10 text-right text-xs font-medium text-slate-500">{pct}%</span>
      </div>

      {stepLabel && job.status === "RUNNING" && (
        <p className="mt-1.5 text-xs text-primary-700">{stepLabel}…</p>
      )}
      {job.error_message && (
        <p className="mt-1.5 text-xs text-red-600" role="alert">
          {job.error_message}
        </p>
      )}
    </div>
  );
}
