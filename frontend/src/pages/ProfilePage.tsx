import { ChangeEvent, FormEvent, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Atom, FileUp, History, Trash2 } from "lucide-react";
import { api, apiError } from "../lib/api";
import type { ProfileDetail, ResearchProfile } from "../lib/types";
import { DNA_FIELDS } from "../lib/types";
import { useWorkspaceStore } from "../stores/workspace";
import { Badge, EmptyState, ErrorState, PageSpinner } from "../components/ui";

export default function ProfilePage() {
  const active = useWorkspaceStore((s) => s.active);
  const wid = active?.id;
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const profilesQ = useQuery<ResearchProfile[]>({
    queryKey: ["profiles", wid],
    queryFn: async () => (await api.get(`/research-profiles?workspace_id=${wid}`)).data,
    enabled: !!wid,
  });

  const detailQ = useQuery<ProfileDetail>({
    queryKey: ["profile", selectedId],
    queryFn: async () => (await api.get(`/research-profiles/${selectedId}?workspace_id=${wid}`)).data,
    enabled: !!selectedId,
  });

  const uploadQ = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return (await api.post<ProfileDetail>(`/research-profiles/upload?workspace_id=${wid}`, form)).data;
    },
    onSuccess: (data) => {
      setUploadError(null);
      setSelectedId(data.id);
      qc.invalidateQueries({ queryKey: ["profiles", wid] });
    },
    onError: (err) => setUploadError(apiError(err)),
  });

  function onFile(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) uploadQ.mutate(f);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    fileRef.current?.click();
  }

  if (!wid) return <EmptyState title="Select a workspace first" />;

  const profiles = profilesQ.data ?? [];
  const current = detailQ.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Research Profile</h1>
        <p className="text-sm text-slate-500">
          Upload a CV to extract your Research DNA — domains, methods, datasets, and interests.
        </p>
      </div>

      <div className="card p-5">
        <form onSubmit={onSubmit} className="flex flex-wrap items-center gap-3" data-testid="cv-upload">
          <FileUp size={18} className="text-primary-600" />
          <div className="text-sm text-slate-600">
            Upload CV (.pdf, .docx, .txt) — parsed locally, never executed.
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={onFile}
          />
          <button type="submit" disabled={uploadQ.isPending} className="btn-primary ml-auto">
            {uploadQ.isPending ? "Extracting DNA…" : "Upload CV"}
          </button>
        </form>
        {uploadError && (
          <div className="mt-3">
            <ErrorState message={uploadError} />
          </div>
        )}
      </div>

      {profilesQ.isLoading ? (
        <PageSpinner />
      ) : profiles.length === 0 ? (
        <EmptyState
          icon={<Atom size={40} />}
          title="No research profile yet"
          hint="Upload your CV above to build your first Research DNA profile."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <div className="card divide-y divide-slate-100">
            {profiles.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedId(p.id)}
                className={`block w-full px-4 py-3 text-left hover:bg-slate-50 ${
                  selectedId === p.id || (!selectedId && p === profiles[0]) ? "bg-primary-50/60" : ""
                }`}
              >
                <p className="line-clamp-1 text-sm font-medium text-slate-800">{p.name}</p>
                <p className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                  <Badge>{p.source_type}</Badge> v{p.current_version}
                </p>
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {!current ? (
              <EmptyState title="Select a profile to view its Research DNA" />
            ) : (
              <>
                <div className="card p-5">
                  <h2 className="mb-3 text-sm font-semibold text-slate-700">{current.name}</h2>
                  <div className="grid gap-4 md:grid-cols-2">
                    {DNA_FIELDS.filter((f) => (current.dna[f.key] ?? []).length > 0).map((f) => (
                      <div key={f.key}>
                        <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                          {f.label}
                        </h3>
                        <div className="flex flex-wrap gap-1.5">
                          {(current.dna[f.key] ?? []).map((v, i) => (
                            <span
                              key={`${f.key}-${i}`}
                              className="rounded-full border border-primary-200 bg-primary-50 px-2.5 py-0.5 text-xs text-primary-800"
                            >
                              {v}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                    {DNA_FIELDS.every((f) => (current.dna[f.key] ?? []).length === 0) && (
                      <p className="text-sm text-slate-400">No DNA fields extracted.</p>
                    )}
                  </div>
                </div>

                <div className="card p-5">
                  <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <History size={15} /> Version history
                  </h3>
                  <ul className="space-y-1.5 text-sm text-slate-600">
                    {[...current.versions].reverse().map((v) => (
                      <li key={v.id} className="flex justify-between rounded px-2 py-1 hover:bg-slate-50">
                        <span>v{v.version}</span>
                        <span className="text-xs text-slate-400">
                          {new Date(v.created_at).toLocaleString()}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                <DeleteCvButton profileId={current.id} workspaceId={wid!} />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DeleteCvButton({ profileId, workspaceId }: { profileId: string; workspaceId: string }) {
  const qc = useQueryClient();
  const del = useMutation({
    mutationFn: async () =>
      api.delete(`/research-profiles/${profileId}/cv?workspace_id=${workspaceId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profiles", workspaceId] });
      qc.removeQueries({ queryKey: ["profile", profileId] });
    },
  });
  return (
    <button onClick={() => del.mutate()} disabled={del.isPending} className="btn-danger w-fit">
      <Trash2 size={15} /> Delete uploaded CV (privacy)
    </button>
  );
}
