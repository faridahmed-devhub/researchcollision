import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import type { GapDetail, Gap } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, ConfidenceBar, EmptyState, PageSpinner } from "../components/ui";

export default function GapsPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;

  const q = useQuery<Gap[]>({
    queryKey: ["gaps", wid],
    queryFn: async () => (await api.get(`/workspaces/${wid}/gaps`)).data,
    enabled: !!wid,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;

  const gaps = q.data ?? [];
  if (gaps.length === 0) {
    return (
      <EmptyState
        icon={<ShieldCheck size={40} />}
        title="No research gaps detected yet"
        hint="Gaps are detected during discovery runs by cross-referencing both researchers' literature."
      />
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-800">Research Gaps</h1>
      <div className="grid gap-3">
        {gaps.map((g) => (
          <GapCard key={g.id} gap={g} workspaceId={wid} />
        ))}
      </div>
    </div>
  );
}

function GapCard({ gap, workspaceId }: { gap: Gap; workspaceId: string }) {
  const detailQ = useQuery<GapDetail>({
    queryKey: ["gap", workspaceId, gap.id],
    queryFn: async () => (await api.get(`/workspaces/${workspaceId}/gaps/${gap.id}`)).data,
  });

  return (
    <details className="card p-4">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{gap.gap_type}</Badge>
          <Badge status={gap.status}>{gap.status}</Badge>
        </div>
        <p className="mt-2 text-sm leading-snug text-slate-700">{gap.description}</p>
        <div className="mt-3 max-w-xs">
          <ConfidenceBar label="Confidence" value={gap.confidence} color="bg-sky-500" />
        </div>
      </summary>
      {detailQ.data && detailQ.data.evidence.length > 0 && (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Supporting evidence
          </h3>
          <ul className="space-y-2">
            {detailQ.data.evidence.map((ev) => (
              <li key={ev.id} className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                <span className="mr-2 font-medium">{ev.status}</span>
                {ev.claim}
              </li>
            ))}
          </ul>
        </div>
      )}
    </details>
  );
}
