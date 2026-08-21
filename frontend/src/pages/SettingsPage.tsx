import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Plus, Trash2 } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { Workspace } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { ErrorState } from "../components/ui";

const WEIGHT_KEYS = [
  "topic_overlap",
  "method_complementarity",
  "career_stage_alignment",
  "trajectory_momentum",
];

export default function SettingsPage() {
  const qc = useQueryClient();
  const setActive = useWorkspaceStore((s) => s.setActive);
  const active = useWorkspaceStore((s) => s.active);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const workspacesQ = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: async () => (await api.get("/workspaces")).data,
  });

  const settingsQ = useQuery<{ collaboration_weights: Record<string, number>; discovery_mode: string }>({
    queryKey: ["settings", active?.id],
    queryFn: async () => (await api.get(`/workspaces/${active!.id}/settings`)).data,
    enabled: !!active?.id,
  });

  const createQ = useMutation({
    mutationFn: async () =>
      (await api.post<Workspace>("/workspaces", { name, description: description || null })).data,
    onSuccess: (ws) => {
      setName("");
      setDescription("");
      setError(null);
      setActive(ws);
      qc.invalidateQueries({ queryKey: ["workspaces"] });
    },
    onError: (err) => setError(apiError(err)),
  });

  const deleteQ = useMutation({
    mutationFn: async (id: string) => api.delete(`/workspaces/${id}`),
    onSuccess: (_d, id) => {
      if (active?.id === id) setActive(null);
      qc.invalidateQueries({ queryKey: ["workspaces"] });
    },
    onError: (err) => setError(apiError(err)),
  });

  const weightsQ = useMutation({
    mutationFn: async (weights: Record<string, number>) =>
      (await api.put(`/workspaces/${active!.id}/settings`, { collaboration_weights: weights })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", active?.id] }),
  });

  function submitCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    createQ.mutate();
  }

  function exportData() {
    if (!active) return;
    window.open(`/api/v1/workspaces/${active.id}/export`, "_blank");
  }

  const weights = settingsQ.data?.collaboration_weights ?? {};

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Settings</h1>
        <p className="text-sm text-slate-500">Workspaces and discovery tuning.</p>
      </div>

      {error && <ErrorState message={error} />}

      <section className="card p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Workspaces</h2>
        <ul className="divide-y divide-slate-100">
          {(workspacesQ.data ?? []).map((w) => (
            <li key={w.id} className="flex items-center gap-3 py-2.5">
              <button
                onClick={() => setActive(w)}
                className={`flex-1 rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-50 ${
                  active?.id === w.id ? "bg-primary-50/70 font-medium text-primary-800" : "text-slate-700"
                }`}
              >
                {w.name}
                {w.description && (
                  <span className="ml-2 text-xs font-normal text-slate-400">{w.description}</span>
                )}
              </button>
              <button
                onClick={() => {
                  if (confirm(`Delete workspace “${w.name}” and all its data?`)) deleteQ.mutate(w.id);
                }}
                className="btn-danger !px-2 !py-1.5"
                aria-label={`Delete ${w.name}`}
              >
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>

        <form onSubmit={submitCreate} className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
          <input
            className="input flex-1"
            placeholder="New workspace name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            className="input flex-1"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={createQ.isPending}>
            <Plus size={15} /> Create
          </button>
        </form>
      </section>

      <section className="card p-5">
        <h2 className="mb-1 text-sm font-semibold text-slate-700">Collaboration score weights</h2>
        <p className="mb-4 text-xs text-slate-500">
          Applied to the next discovery run in <b>{active?.name ?? "—"}</b>.
        </p>
        <div className="space-y-4">
          {WEIGHT_KEYS.map((k) => (
            <div key={k}>
              <label className="mb-1 flex justify-between text-xs font-medium capitalize text-slate-600">
                <span>{k.replace(/_/g, " ")}</span>
                <span data-testid={`weight-${k}`}>{Math.round((weights[k] ?? 0) * 100)}%</span>
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={weights[k] ?? 0}
                disabled={!active || weightsQ.isPending}
                onChange={(e) =>
                  weightsQ.mutate({ ...weights, [k]: Number(e.target.value) })
                }
                onMouseUp={() => weightsQ.reset()}
                onTouchEnd={() => weightsQ.reset()}
                className="w-full accent-primary-600"
              />
            </div>
          ))}
        </div>
      </section>

      <section className="card p-5">
        <h2 className="mb-1 text-sm font-semibold text-slate-700">Data export</h2>
        <p className="mb-4 text-xs text-slate-500">
          Download everything stored for this workspace as JSON (privacy / GDPR-style export).
        </p>
        <button onClick={exportData} disabled={!active} className="btn-secondary">
          <Download size={15} /> Export workspace JSON
        </button>
      </section>
    </div>
  );
}
