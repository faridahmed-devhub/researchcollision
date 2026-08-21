import { FormEvent, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Search } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { Paper } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, ErrorState, PageSpinner } from "../components/ui";

export default function LiteraturePage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;
  const [q, setQ] = useState("");
  const [submitted, setSubmitted] = useState("");

  const searchQ = useQuery<Paper[]>({
    queryKey: ["paper-search", wid, submitted],
    queryFn: async () =>
      (
        await api.get(
          `/papers/search?q=${encodeURIComponent(submitted)}&workspace_id=${wid}&limit=20`
        )
      ).data,
    enabled: !!wid && submitted.length > 0,
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(q.trim());
  }

  if (!wid) return <EmptyState title="Select a workspace first" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Literature</h1>
        <p className="text-sm text-slate-500">
          Search across providers (OpenAlex → Semantic Scholar → Crossref → arXiv) with automatic
          fallback.
        </p>
      </div>

      <form onSubmit={submit} className="card flex gap-2 p-4" data-testid="literature-search">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="input pl-9"
            placeholder="e.g. low-resource machine translation"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={!q.trim()}>
          Search
        </button>
      </form>

      {searchQ.isFetching && <PageSpinner />}
      {searchQ.error && <ErrorState message={apiError(searchQ.error)} />}

      {!searchQ.isFetching && submitted && (searchQ.data ?? []).length === 0 && !searchQ.error && (
        <EmptyState icon={<BookOpen size={40} />} title={`No results for “${submitted}”`} />
      )}

      <div className="grid gap-3">
        {(searchQ.data ?? []).map((p) => (
          <article key={p.id} className="card p-4">
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-sm font-medium leading-snug text-slate-800">{p.title}</h2>
              <div className="flex shrink-0 gap-1.5">
                {p.is_synthetic && <Badge status="UNKNOWN">synthetic</Badge>}
                <Badge>{p.source_provider}</Badge>
              </div>
            </div>
            {p.abstract && (
              <p className="mt-2 line-clamp-2 text-xs text-slate-500">{p.abstract}</p>
            )}
            <p className="mt-2 text-xs text-slate-400">
              {[p.venue, p.publication_year, `${p.citation_count} citations`]
                .filter(Boolean)
                .join(" · ")}
              {p.doi ? ` · DOI ${p.doi}` : ""}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}
