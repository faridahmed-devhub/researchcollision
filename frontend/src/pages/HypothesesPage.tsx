import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Lightbulb } from "lucide-react";
import { api } from "../lib/api";
import type { Hypothesis } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { EmptyState, PageSpinner } from "../components/ui";

export default function HypothesesPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;

  const q = useQuery<Hypothesis[]>({
    queryKey: ["hypotheses", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/hypotheses`)).data,
    enabled: !!wid,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;

  const items = q.data ?? [];
  if (items.length === 0) {
    return (
      <EmptyState
        icon={<Lightbulb size={40} />}
        title="No hypotheses yet"
        hint="Hypotheses are generated from verified intersections during discovery runs."
      />
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-800">Hypotheses</h1>
      <div className="grid gap-3">
        {items.map((h) => (
          <Link
            key={h.id}
            to={`/hypotheses/${h.id}`}
            className="card block p-4 transition-colors hover:border-primary-300"
          >
            <p className="text-sm font-semibold text-slate-800">{h.label}</p>
            <p className="mt-1 line-clamp-2 text-xs text-slate-500">{h.research_question}</p>
            <div className="mt-2 flex gap-4 text-xs text-slate-400">
              <span>confidence {Math.round(h.confidence * 100)}%</span>
              <span>{new Date(h.created_at).toLocaleDateString()}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
