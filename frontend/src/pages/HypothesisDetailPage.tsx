import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FlaskConical, ShieldCheck } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { HypothesisDetail } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { ConfidenceBar, EmptyState, ErrorState, PageSpinner } from "../components/ui";
import { EvidenceList, Section } from "./IntersectionDetailPage";

export default function HypothesisDetailPage() {
  const { id } = useParams();
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;

  const q = useQuery<HypothesisDetail>({
    queryKey: ["hypothesis", wid, id],
    queryFn: async () => (await api.get(`/workspaces/${wid}/hypotheses/${id}`)).data,
    enabled: !!wid && !!id,
  });

  if (!wid) return <EmptyState title="Select a workspace first" />;
  if (q.isLoading) return <PageSpinner />;
  if (q.error) return <ErrorState message={apiError(q.error)} />;
  const h = q.data;
  if (!h) return null;

  return (
    <div className="space-y-6" data-testid="hypothesis-detail">
      <Link to="/hypotheses" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft size={15} /> All hypotheses
      </Link>

      <div className="card p-6">
        <h1 className="text-lg font-semibold text-slate-800">{h.label}</h1>
        <div className="mt-4 max-w-xs">
          <ConfidenceBar label="Confidence" value={h.confidence} color="bg-amber-500" />
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Section title="Research question" body={h.research_question} />
          <Section title="Hypothesis" body={h.hypothesis_text} />
          {h.motivation && <Section title="Motivation" body={h.motivation} />}
          {h.method && <Section title="Method" body={h.method} />}
          {h.dataset && <Section title="Dataset" body={h.dataset} />}
          {h.baseline && <Section title="Baseline" body={h.baseline} />}
          {h.metrics && <Section title="Metrics" body={h.metrics} />}
          {h.expected_contribution && (
            <Section title="Expected contribution" body={h.expected_contribution} />
          )}
          {h.risks && <Section title="Risks" body={h.risks} />}
        </div>
        {h.intersection && (
          <Link
            to={`/intersections/${h.intersection.id}`}
            className="mt-5 inline-block rounded-lg border border-primary-200 bg-primary-50 px-3 py-2 text-xs font-medium text-primary-700 hover:bg-primary-100"
          >
            From intersection: {h.intersection.title}
          </Link>
        )}
      </div>

      {h.experiment && (
        <div className="card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <FlaskConical size={16} className="text-primary-600" /> Experiment design
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {h.experiment.proposed_approach && (
              <Section title="Proposed approach" body={h.experiment.proposed_approach} />
            )}
            {h.experiment.baseline && <Section title="Baseline" body={h.experiment.baseline} />}
            {h.experiment.dataset && (
              <Section
                title={`Dataset (${h.experiment.dataset_status})`}
                body={h.experiment.dataset}
              />
            )}
            {h.experiment.training_setup && (
              <Section title="Training setup" body={h.experiment.training_setup} />
            )}
            {h.experiment.evaluation_setup && (
              <Section title="Evaluation setup" body={h.experiment.evaluation_setup} />
            )}
            {h.experiment.metrics && <Section title="Metrics" body={h.experiment.metrics} />}
            {h.experiment.expected_outcomes && (
              <Section title="Expected outcomes" body={h.experiment.expected_outcomes} />
            )}
            {h.experiment.failure_conditions && (
              <Section title="Failure conditions" body={h.experiment.failure_conditions} />
            )}
          </div>
          {(h.experiment.ablations ?? []).length > 0 && (
            <div className="mt-4">
              <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Ablations
              </h3>
              <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
                {h.experiment.ablations.map((a, i) => (
                  <li key={i}>{typeof a === "string" ? a : JSON.stringify(a)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <ShieldCheck size={16} className="text-emerald-600" /> Evidence
        </h2>
        <EvidenceList evidence={h.evidence} />
      </section>
    </div>
  );
}
