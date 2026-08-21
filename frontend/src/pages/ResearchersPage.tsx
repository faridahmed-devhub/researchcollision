import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, UserPlus } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { Researcher } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, ErrorState } from "../components/ui";

export default function ResearchersPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [name, setName] = useState("");
  const [affiliation, setAffiliation] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const searchQ = useQuery<Researcher[]>({
    queryKey: ["researcher-search", wid, submitted],
    queryFn: async () =>
      (
        await api.get(
          `/researchers/search?q=${encodeURIComponent(submitted)}&workspace_id=${wid}`
        )
      ).data,
    enabled: !!wid && submitted.length > 0,
  });

  const createQ = useMutation({
    mutationFn: async () =>
      (
        await api.post<Researcher>(`/researchers?workspace_id=${wid}`, {
          name,
          affiliation: affiliation || null,
        })
      ).data,
    onSuccess: () => {
      setName("");
      setAffiliation("");
      setFormError(null);
      qc.invalidateQueries({ queryKey: ["researcher-search", wid] });
    },
    onError: (err) => setFormError(apiError(err)),
  });

  function submitSearch(e: FormEvent) {
    e.preventDefault();
    setSubmitted(q.trim());
  }

  function submitCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    createQ.mutate();
  }

  if (!wid) return <EmptyState title="Select a workspace first" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Researchers</h1>
        <p className="text-sm text-slate-500">
          Find researchers to pair in a discovery run — search matches names and aliases.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <form onSubmit={submitSearch} className="card flex gap-2 p-4">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                className="input pl-9"
                placeholder="Search researchers…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={!q.trim()}>
              Search
            </button>
          </form>

          {searchQ.error && <ErrorState message={apiError(searchQ.error)} />}
          {submitted && (searchQ.data ?? []).length === 0 && !searchQ.isFetching && (
            <EmptyState title={`No researchers found for “${submitted}”`} />
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            {(searchQ.data ?? []).map((r) => (
              <article key={r.id} className="card p-4">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-sm font-semibold text-slate-800">{r.name}</h2>
                  {r.is_synthetic && <Badge status="UNKNOWN">synthetic</Badge>}
                </div>
                {r.affiliation && <p className="mt-0.5 text-xs text-slate-500">{r.affiliation}</p>}
                {r.bio && <p className="mt-2 line-clamp-3 text-xs text-slate-500">{r.bio}</p>}
              </article>
            ))}
          </div>
        </div>

        <form onSubmit={submitCreate} className="card h-fit space-y-3 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <UserPlus size={15} /> Add researcher
          </h2>
          {formError && <ErrorState message={formError} />}
          <div>
            <label className="label">Name</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Affiliation</label>
            <input
              className="input"
              value={affiliation}
              onChange={(e) => setAffiliation(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={createQ.isPending}>
            {createQ.isPending ? "Adding…" : "Add researcher"}
          </button>
        </form>
      </div>
    </div>
  );
}
