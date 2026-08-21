import { Navigate, Outlet } from "react-router-dom";

import { useWorkspaceStore } from "../stores/workspace";

export default function RequireWorkspace() {
  const active = useWorkspaceStore((s) => s.active);
  if (!active) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
