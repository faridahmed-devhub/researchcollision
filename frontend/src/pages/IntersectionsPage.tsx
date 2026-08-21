import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { GitBranch } from "lucide-react";
import { api } from "../lib/api";
import type { Intersection } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, PageSpinner } from "../components/ui";

export default function IntersectionsPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;

  const q = useQuery<Intersection[]>({
    queryKey: ["intersections", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/intersections`)).data,
    enabled: !!wid,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;

  const items = q.data ?? [];
  if (items.length === 0) {
    return (
      <EmptyState
        icon={<GitBranch size={40} />}
        title="No intersections yet"
        hint="Run a discovery job to find research intersections between researchers."
      />
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-800">Intersections</h1>
      <div className="grid gap-3">
        {items.map((ix) => (
          <Link
            key={ix.id}
            to={`/intersections/${ix.id}`}
            className="card block p-4 transition-colors hover:border-primary-300"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge status={ix.status}>{ix.status}</Badge>
              <Badge>{ix.discovery_mode}</Badge>
              <span className="ml-auto text-xs text-slate-400">
                {new Date(ix.created_at).toLocaleDateString()}
              </span>
            </div>
            <h2 className="mt-2 text-sm font-semibold leading-snug text-slate-800">{ix.title}</h2>
            <p className="mt-1 line-clamp-2 text-xs text-slate-500">{ix.description}</p>
            <div className="mt-3 flex gap-6 text-xs text-slate-500">
              <span>novelty {Math.round(ix.novelty_confidence * 100)}%</span>
              <span>feasibility {Math.round(ix.feasibility_confidence * 100)}%</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
