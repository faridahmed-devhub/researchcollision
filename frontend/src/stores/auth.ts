import { create } from "zustand";
import type { User } from "../lib/types";

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

const savedToken = localStorage.getItem("rc_token");
let savedUser: User | null = null;
try {
  const raw = localStorage.getItem("rc_user");
  if (raw) savedUser = JSON.parse(raw);
} catch {
  savedUser = null;
}

export const useAuth = create<AuthState>((set) => ({
  token: savedToken,
  user: savedUser,
  setAuth: (token, user) => {
    localStorage.setItem("rc_token", token);
    localStorage.setItem("rc_user", JSON.stringify(user));
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem("rc_token");
    localStorage.removeItem("rc_user");
    set({ token: null, user: null });
  },
}));
