import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuth } from "../stores/auth";
import { useWorkspaceStore } from "../stores/workspace";

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuth.setState({ token: null, user: null });
  });

  it("starts unauthenticated", () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it("setAuth persists token and user", () => {
    const { result } = renderHook(() => useAuth());
    act(() => {
      result.current.setAuth("tok-1", { id: "u1", email: "a@b.dev", name: "A" });
    });
    expect(result.current.token).toBe("tok-1");
    expect(localStorage.getItem("rc_token")).toBe("tok-1");
    expect(JSON.parse(localStorage.getItem("rc_user")!)).toMatchObject({ id: "u1" });
  });

  it("logout clears state and storage", () => {
    const { result } = renderHook(() => useAuth());
    act(() => {
      result.current.setAuth("tok-2", { id: "u2", email: "c@d.dev", name: "C" });
      result.current.logout();
    });
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem("rc_token")).toBeNull();
  });
});

describe("workspace store", () => {
  it("setActive persists workspace", () => {
    const { result } = renderHook(() => useWorkspaceStore());
    const ws = { id: "w1", name: "WS", description: null, discovery_mode: "normal", created_at: "", updated_at: "" };
    act(() => result.current.setActive(ws));
    expect(result.current.active?.id).toBe("w1");
    expect(JSON.parse(localStorage.getItem("rc_workspace")!)).toMatchObject({ id: "w1" });
    act(() => result.current.setActive(null));
    expect(localStorage.getItem("rc_workspace")).toBeNull();
  });
});
