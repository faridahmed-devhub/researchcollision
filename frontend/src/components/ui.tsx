import { clsx } from "clsx";
import type { EvidenceStatus } from "../lib/types";

const STATUS_STYLES: Record<string, string> = {
  VERIFIED: "bg-emerald-100 text-emerald-800 border-emerald-200",
  INFERRED: "bg-sky-100 text-sky-800 border-sky-200",
  SPECULATIVE: "bg-amber-100 text-amber-800 border-amber-200",
  UNKNOWN: "bg-slate-100 text-slate-600 border-slate-200",
  UNVERIFIED: "bg-orange-100 text-orange-800 border-orange-200",
  COMPLETED: "bg-emerald-100 text-emerald-800 border-emerald-200",
  RUNNING: "bg-primary-100 text-primary-800 border-primary-200 animate-pulse",
  PENDING: "bg-slate-100 text-slate-600 border-slate-200",
  PAUSED: "bg-yellow-100 text-yellow-800 border-yellow-200",
  FAILED: "bg-red-100 text-red-700 border-red-200",
  CANCELLED: "bg-slate-100 text-slate-500 border-slate-200",
};

export function Badge({
  children,
  status,
  className,
}: {
  children: React.ReactNode;
  status?: string;
  className?: string;
}) {
  const style = status ? STATUS_STYLES[status] : "bg-slate-100 text-slate-700 border-slate-200";
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        style,
        className
      )}
    >
      {children}
    </span>
  );
}

export function EvidenceBadge({ status }: { status: EvidenceStatus }) {
  return <Badge status={status}>{status}</Badge>;
}

export function ConfidenceBar({
  label,
  value,
  color = "bg-primary-500",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs font-medium text-slate-500">
        <span>{label}</span>
        <span data-testid={`confidence-${label.toLowerCase().replace(/\s+/g, "-")}`}>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className={clsx("h-full rounded-full transition-all", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={clsx(
        "inline-block h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-primary-600",
        className
      )}
      role="status"
      aria-label="Loading"
    />
  );
}

export function PageSpinner() {
  return (
    <div className="flex h-64 items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  hint,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  hint?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center justify-center gap-2 p-10 text-center">
      {icon && <div className="text-slate-300">{icon}</div>}
      <p className="font-medium text-slate-700">{title}</p>
      {hint && <p className="max-w-md text-sm text-slate-500">{hint}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
      {message}
    </div>
  );
}

export function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
}) {
  return (
    <div className="card flex items-center gap-4 p-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
        {icon}
      </div>
      <div>
        <p className="text-2xl font-semibold leading-tight" data-testid={`stat-${label}`}>
          {value}
        </p>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      </div>
    </div>
  );
}
