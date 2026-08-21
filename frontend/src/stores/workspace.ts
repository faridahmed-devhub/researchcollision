import { create } from "zustand";
import type { Workspace } from "../lib/types";

interface WorkspaceState {
  active: Workspace | null;
  setActive: (ws: Workspace | null) => void;
}

const saved = (() => {
  try {
    const raw = localStorage.getItem("rc_workspace");
    return raw ? (JSON.parse(raw) as Workspace) : null;
  } catch {
    return null;
  }
})();

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  active: saved,
  setActive: (ws) => {
    if (ws) localStorage.setItem("rc_workspace", JSON.stringify(ws));
    else localStorage.removeItem("rc_workspace");
    set({ active: ws });
  },
}));
