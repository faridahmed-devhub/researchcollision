import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import type { Evidence, EvidenceStatus } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { EmptyState, PageSpinner } from "../components/ui";
import { EvidenceList } from "./IntersectionDetailPage";

const STATUSES: (EvidenceStatus | "ALL")[] = [
  "ALL",
  "VERIFIED",
  "INFERRED",
  "SPECULATIVE",
  "UNVERIFIED",
  "UNKNOWN",
];

export default function EvidencePage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;
  const [status, setStatus] = useState<EvidenceStatus | "ALL">("ALL");

  const q = useQuery<Evidence[]>({
    queryKey: ["evidence", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/evidence?limit=500`)).data,
    enabled: !!wid,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;

  const all = q.data ?? [];
  const filtered = status === "ALL" ? all : all.filter((e) => e.status === status);

  const counts = Object.fromEntries(
    STATUSES.map((s) => [s, s === "ALL" ? all.length : all.filter((e) => e.status === s).length])
  );

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Evidence Explorer</h1>
        <p className="text-sm text-slate-500">
          Every claim in this workspace with its verification status and source.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              status === s
                ? "border-primary-600 bg-primary-600 text-white"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {s} ({counts[s]})
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<ShieldCheck size={40} />}
          title="No evidence recorded yet"
          hint="Evidence is collected and verified during discovery runs."
        />
      ) : (
        <EvidenceList evidence={filtered} />
      )}
    </div>
  );
}
