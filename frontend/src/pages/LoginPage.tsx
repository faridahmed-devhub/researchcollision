import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Atom } from "lucide-react";
import { api, apiError } from "../lib/api";
import { useAuth } from "../stores/auth";
import type { TokenResponse } from "../lib/types";

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuth((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api.post<TokenResponse>("/auth/login", { email, password });
      setAuth(res.data.access_token, res.data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-3 text-white">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-600">
            <Atom size={24} />
          </div>
          <h1 className="text-2xl font-semibold">ResearchCollision</h1>
        </div>
        <form onSubmit={submit} className="card space-y-4 p-6" data-testid="login-form">
          <h2 className="text-lg font-semibold text-slate-800">Sign in</h2>
          {error && (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert">
              {error}
            </p>
          )}
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          <button type="submit" disabled={busy} className="btn-primary w-full">
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <button
            type="button"
            className="btn-secondary w-full"
            onClick={() => {
              setEmail("demo@researchcollision.dev");
              setPassword("demo1234");
            }}
          >
            Use demo credentials
          </button>
          <p className="text-center text-sm text-slate-500">
            No account?{" "}
            <Link to="/register" className="font-medium text-primary-600 hover:underline">
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
