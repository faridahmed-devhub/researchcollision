import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge, ConfidenceBar, EmptyState, StatCard } from "../components/ui";

describe("ui components", () => {
  it("renders badge with status styling", () => {
    render(<Badge status="VERIFIED">VERIFIED</Badge>);
    const b = screen.getByText("VERIFIED");
    expect(b).toBeInTheDocument();
    expect(b.className).toContain("emerald");
  });

  it("renders confidence bar with percentage", () => {
    render(<ConfidenceBar label="Novelty" value={0.55} />);
    expect(screen.getByText("Novelty")).toBeInTheDocument();
    expect(screen.getByTestId("confidence-novelty")).toHaveTextContent("55%");
  });

  it("renders stat card value and label", () => {
    render(<StatCard icon={null} label="papers" value={12} />);
    expect(screen.getByTestId("stat-papers")).toHaveTextContent("12");
  });

  it("renders empty state with hint", () => {
    render(<EmptyState title="Nothing here" hint="Try something else" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Try something else")).toBeInTheDocument();
  });
});
