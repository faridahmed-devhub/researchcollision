import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileText, RefreshCw } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { DiscoveryJob, PaperDraft } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, ErrorState, PageSpinner } from "../components/ui";

export default function PaperDraftPage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;
  const qc = useQueryClient();
  const [jobId, setJobId] = useState<string>("");
  const [actionError, setActionError] = useState<string | null>(null);

  const jobsQ = useQuery<DiscoveryJob[]>({
    queryKey: ["jobs", wid],
    queryFn: async () => (await api.get(`/discovery/workspaces/${wid}/jobs`)).data,
    enabled: !!wid,
  });

  useEffect(() => {
    if (!jobId && jobsQ.data?.length) {
      const completed = jobsQ.data
        .filter((j) => j.status === "COMPLETED" || j.status === "FAILED")
        .sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      const fallback = jobsQ.data
        .slice()
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setJobId((completed[0] ?? fallback[0]).id);
    }
  }, [jobsQ.data, jobId]);

  const draftQ = useQuery<PaperDraft | null>({
    queryKey: ["paper-draft", wid, jobId],
    queryFn: async () => {
      if (!jobId) return null;
      try {
        return (await api.get<PaperDraft>(`/discovery/jobs/${jobId}/paper-draft`)).data;
      } catch (err) {
        const status = (err as { response?: { status?: number } }).response?.status;
        if (status === 404) return null; // not generated yet for this job
        throw err;
      }
    },
    enabled: !!wid && !!jobId,
  });

  const generate = useMutation({
    mutationFn: async () =>
      (await api.post<PaperDraft>(`/discovery/jobs/${jobId}/paper-draft`)).data,
    onSuccess: () => {
      setActionError(null);
      qc.invalidateQueries({ queryKey: ["paper-draft", wid, jobId] });
      qc.invalidateQueries({ queryKey: ["jobs", wid] });
    },
    onError: (err) => setActionError(apiError(err)),
  });

  async function download(format: "markdown" | "pdf") {
    if (!jobId) return;
    setActionError(null);
    try {
      const res = await api.get(`/discovery/jobs/${jobId}/paper-draft/export`, {
        params: { format },
        responseType: "blob",
      });
      const disposition = res.headers["content-disposition"] ?? "";
      const match = /\bfilename="?([^";]+)"?/.exec(disposition);
      const filename = match?.[1] ?? `paper-draft.${format === "pdf" ? "pdf" : "md"}`;
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setActionError(apiError(err));
    }
  }

  if (!wid) return <EmptyState title="Select a workspace first" />;

  const jobs = jobsQ.data ?? [];
  const draft = draftQ.data ?? null;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Paper Draft</h1>
        <p className="text-sm text-slate-500">
          AI-generated research-paper draft for a discovery job — a proposal grounded in
          stored evidence, never a report of measured results.
        </p>
      </div>

      <div className="card flex flex-wrap items-end gap-3 p-4">
        <div className="min-w-64 flex-1">
          <label className="label" htmlFor="draft-job">
            Discovery job
          </label>
          <select
            id="draft-job"
            className="input"
            value={jobId}
            onChange={(e) => {
              setJobId(e.target.value);
              qc.invalidateQueries({ queryKey: ["paper-draft", wid] });
            }}
          >
            {jobs.length === 0 && <option value="">No jobs yet</option>}
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.status} · {new Date(j.created_at).toLocaleString()}
              </option>
            ))}
          </select>
        </div>
        <button
          className="btn-primary"
          disabled={!jobId || generate.isPending}
          onClick={() => generate.mutate()}
        >
          <RefreshCw size={15} /> {generate.isPending ? "Generating…" : "Generate / regenerate"}
        </button>
        <button
          className="btn-secondary"
          disabled={!draft}
          onClick={() => download("markdown")}
        >
          <Download size={15} /> Markdown
        </button>
        <button
          className="btn-secondary"
          disabled={!draft}
          onClick={() => download("pdf")}
        >
          <Download size={15} /> PDF
        </button>
      </div>

      {actionError && <ErrorState message={actionError} />}

      {draftQ.isLoading || generate.isPending ? (
        <PageSpinner />
      ) : draft ? (
        <PaperDraftView draft={draft} />
      ) : (
        <EmptyState
          icon={<FileText size={40} />}
          title="No paper draft for this job yet"
          hint="Run a discovery job to completion, or click “Generate / regenerate” to create a draft."
        />
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card p-5">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-primary-700">
        {title}
      </h2>
      <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
        {children}
      </div>
    </section>
  );
}

function PaperDraftView({ draft }: { draft: PaperDraft }) {
  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="mb-3">
          <Badge>{draft.draft_status}</Badge>
        </div>
        <h2 className="text-2xl font-semibold text-slate-900">{draft.title}</h2>
        <p className="mt-1 text-xs text-slate-400">
          Generated {new Date(draft.created_at).toLocaleString()} · report{" "}
          <span className="font-mono">{draft.report_id}</span>
        </p>
      </div>

      <Section title="Abstract">{draft.abstract}</Section>
      <Section title="1. Introduction">{draft.introduction}</Section>
      <Section title="2. Related Work">{draft.related_work}</Section>
      <Section title="3. Research Gap">{draft.research_gap}</Section>
      <Section title="4. Research Question & Hypothesis">
        <p>
          <b>Research question:</b> {draft.research_question}
        </p>
        <p className="mt-2">
          <b>Hypothesis:</b> {draft.hypothesis}
        </p>
      </Section>
      <Section title="5. Methodology">{draft.methodology}</Section>
      <Section title="6. Experiment Design">{draft.experiment_design}</Section>
      <Section title="7. Expected Results">
        <p className="mb-2 text-xs font-semibold italic text-amber-700">
          ({draft.expected_results_label})
        </p>
        {draft.expected_results}
      </Section>
      <Section title="8. Limitations">
        <ul className="list-disc space-y-1 pl-5">
          {draft.limitations.map((lim, i) => (
            <li key={i}>{lim}</li>
          ))}
        </ul>
      </Section>
      <Section title="9. Conclusion">{draft.conclusion}</Section>

      {draft.citations.length > 0 && (
        <Section title="References (grounded in stored evidence)">
          <ul className="space-y-1.5">
            {draft.citations.map((c) => (
              <li key={c.number} className="flex gap-2">
                <span className="shrink-0 font-mono text-xs text-slate-400">
                  [{c.number}]
                </span>
                <span>
                  {c.text} <Badge status={c.status}>{c.status}</Badge>
                </span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {draft.evidence.length > 0 && (
        <Section title="Grounding Evidence">
          <p className="mb-3 text-xs text-slate-500">
            Every claim in this draft traces to stored evidence:
          </p>
          <ul className="space-y-2">
            {draft.evidence.map((e) => (
              <li key={e.evidence_id} className="flex flex-col gap-0.5">
                <span className="flex items-center gap-2">
                  <Badge status={e.status}>{e.status}</Badge>
                  <span className="font-mono text-[10px] text-slate-400">{e.evidence_id}</span>
                </span>
                <span className="text-sm text-slate-700">{e.claim}</span>
                {e.source_title && <span className="text-xs text-slate-500">{e.source_title}</span>}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}