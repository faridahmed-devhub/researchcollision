import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { api } from "../lib/api";
import type { Collaboration } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, PageSpinner } from "../components/ui";

const CATEGORY_STYLES: Record<string, string> = {
  Exploratory: "bg-violet-100 text-violet-800 border-violet-200",
  Complementary: "bg-sky-100 text-sky-800 border-sky-200",
  Confirmatory: "bg-emerald-100 text-emerald-800 border-emerald-200",
};

export default function CollaborationsPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;

  const q = useQuery<Collaboration[]>({
    queryKey: ["collaborations", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/collaborations`)).data,
    enabled: !!wid,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;

  const items = q.data ?? [];
  if (items.length === 0) {
    return (
      <EmptyState
        icon={<Users size={40} />}
        title="No collaboration candidates yet"
        hint="Candidates are ranked after each discovery run using configurable weights."
      />
    );
  }

  const maxScore = Math.max(...items.map((c) => c.score), 1);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Collaboration Candidates</h1>
        <p className="text-sm text-slate-500">
          Ranked by weighted score — tune weights in Settings.
        </p>
      </div>
      <div className="grid gap-3">
        {items.map((c, idx) => (
          <article key={c.id} className="card p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-lg font-bold text-primary-600">#{idx + 1}</span>
              <Badge className={CATEGORY_STYLES[c.category] ?? ""}>{c.category}</Badge>
              <span className="ml-auto text-sm font-semibold text-slate-700">
                score {Math.round(c.score * 10) / 10}
              </span>
            </div>

            <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary-400 to-primary-600"
                style={{ width: `${(c.score / maxScore) * 100}%` }}
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-500">
              {Object.entries(c.component_scores ?? {}).map(([k, v]) => (
                <span key={k}>
                  {k.replace(/_/g, " ")}: <b className="text-slate-700">{Math.round(v * 100)}%</b>
                </span>
              ))}
            </div>

            {c.rationale && (
              <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-slate-600">{c.rationale}</p>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
