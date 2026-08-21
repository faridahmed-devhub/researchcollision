import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, Lightbulb, ShieldCheck } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { IntersectionDetail } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, ConfidenceBar, EmptyState, ErrorState, EvidenceBadge, PageSpinner } from "../components/ui";

export default function IntersectionDetailPage() {
  const { id } = useParams();
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;

  const q = useQuery<IntersectionDetail>({
    queryKey: ["intersection", wid, id],
    queryFn: async () =>
      (await api.get(`/workspaces/${wid}/intersections/${id}`)).data,
    enabled: !!wid && !!id,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;
  if (q.error) return <ErrorState message={apiError(q.error)} />;
  const ix = q.data;
  if (!ix) return null;

  return (
    <div className="space-y-6" data-testid="intersection-detail">
      <Link to="/intersections" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft size={15} /> All intersections
      </Link>

      <div className="card p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge status={ix.status}>{ix.status}</Badge>
          <Badge>{ix.discovery_mode}</Badge>
          <span className="ml-auto text-xs text-slate-400">
            {new Date(ix.created_at).toLocaleString()}
          </span>
        </div>
        <h1 className="mt-3 text-lg font-semibold leading-snug text-slate-800">{ix.title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">{ix.description}</p>

        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <ConfidenceBar label="Novelty" value={ix.novelty_confidence} />
          <ConfidenceBar label="Feasibility" value={ix.feasibility_confidence} color="bg-emerald-500" />
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {ix.researcher_a && (
            <ResearcherCard role="A" name={ix.researcher_a.name} affiliation={ix.researcher_a.affiliation} why={ix.why_researcher_a} />
          )}
          {ix.researcher_b && (
            <ResearcherCard role="B" name={ix.researcher_b.name} affiliation={ix.researcher_b.affiliation} why={ix.why_researcher_b} />
          )}
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {ix.shared_problem && (
            <Section title="Shared problem" body={ix.shared_problem} />
          )}
          {ix.complementary_expertise && (
            <Section title="Complementary expertise" body={ix.complementary_expertise} />
          )}
          {ix.gap_description && <Section title="Underlying gap" body={ix.gap_description} />}
        </div>
      </div>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Lightbulb size={16} className="text-amber-500" /> Hypotheses ({ix.hypotheses.length})
        </h2>
        {ix.hypotheses.length === 0 ? (
          <EmptyState title="No hypotheses generated for this intersection." />
        ) : (
          <div className="grid gap-3">
            {ix.hypotheses.map((h) => (
              <Link
                key={h.id}
                to={`/hypotheses/${h.id}`}
                className="card block p-4 transition-colors hover:border-primary-300"
              >
                <p className="text-sm font-semibold text-slate-800">{h.label}</p>
                <p className="mt-1 line-clamp-2 text-xs text-slate-500">{h.research_question}</p>
                <p className="mt-2 text-xs text-slate-400">confidence {Math.round(h.confidence * 100)}%</p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <ShieldCheck size={16} className="text-emerald-600" /> Supporting evidence ({ix.evidence.length})
        </h2>
        <EvidenceList evidence={ix.evidence} />
      </section>
    </div>
  );
}

function ResearcherCard({
  role,
  name,
  affiliation,
  why,
}: {
  role: string;
  name: string;
  affiliation?: string | null;
  why: string | null;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-600">Researcher {role}</p>
      <p className="mt-1 text-sm font-semibold text-slate-800">{name}</p>
      {affiliation && <p className="text-xs text-slate-500">{affiliation}</p>}
      {why && <p className="mt-2 text-xs leading-relaxed text-slate-600">{why}</p>}
    </div>
  );
}

export function Section({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</h3>
      <p className="text-sm leading-relaxed text-slate-600">{body}</p>
    </div>
  );
}

export function EvidenceList({ evidence }: { evidence: import("../lib/types").Evidence[] }) {
  if (evidence.length === 0) {
    return <EmptyState title="No evidence recorded." hint="Every claim should link to verifiable sources." />;
  }
  return (
    <div className="space-y-2">
      {evidence.map((ev) => (
        <article key={ev.id} className="card p-4">
          <div className="flex flex-wrap items-center gap-2">
            <EvidenceBadge status={ev.status} />
            <span className="text-xs text-slate-400">confidence {Math.round(ev.confidence * 100)}%</span>
            {ev.source_url && (
              <a
                href={ev.source_url}
                target="_blank"
                rel="noreferrer"
                className="ml-auto inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:underline"
              >
                source <ExternalLink size={12} />
              </a>
            )}
          </div>
          <p className="mt-2 text-sm text-slate-700">{ev.claim}</p>
          {ev.evidence_text && (
            <p className="mt-1 line-clamp-3 text-xs italic text-slate-500">“{ev.evidence_text}”</p>
          )}
          {ev.source_title && <p className="mt-1.5 text-xs text-slate-400">— {ev.source_title}</p>}
        </article>
      ))}
    </div>
  );
}
