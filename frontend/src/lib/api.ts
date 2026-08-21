import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("rc_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config?.url?.includes("/auth/")) {
      localStorage.removeItem("rc_token");
      localStorage.removeItem("rc_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export function apiError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data;
    if (detail?.error?.message) return detail.error.message as string;
    if (detail?.detail) {
      if (typeof detail.detail === "string") return detail.detail;
      if (Array.isArray(detail.detail)) {
        const first = detail.detail[0];
        return first?.msg ? String(first.msg) : "Validation error";
      }
    }
    return err.message;
  }
  return String(err);
}
