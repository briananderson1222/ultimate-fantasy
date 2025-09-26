import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

// Mock react-query useMutation to avoid network
vi.mock("@tanstack/react-query", async () => {
  const original =
    await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...original,
    useMutation: () => ({ mutate: vi.fn(), isPending: false, isError: false, error: undefined }),
  } as any;
});

// Mock next/navigation useParams
vi.mock("next/navigation", () => ({ useParams: () => ({ leagueId: "L-1" }) }));

import Page from "../../src/app/leagues/[leagueId]/settings/page";
import { ToastProvider } from "../../src/components/ui/toast";

describe("Rule Editor presets import/export + diff", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("shows a diff when JSON differs from active rules", () => {
    // Seed an "active" value
    localStorage.setItem("uf_rules:L-1:scoring.basketball", JSON.stringify({ PTS: 1 }, null, 2));

    render(
      <ToastProvider>
        <Page />
      </ToastProvider>,
    );

    // Change JSON to include a change and an addition
    const ta = screen.getByLabelText("Value (JSON)");
    fireEvent.change(ta, { target: { value: JSON.stringify({ PTS: 2, REB: 1 }, null, 2) } });

    // Diff should show PTS changed and REB added
    expect(screen.getByText(/Changed/i)).toBeInTheDocument();
    expect(screen.getByText(/PTS: 1/)).toBeInTheDocument();
    expect(screen.getByText(/→/)).toBeInTheDocument();
    expect(screen.getByText(/Added/i)).toBeInTheDocument();
    expect(screen.getByText(/REB/)).toBeInTheDocument();
  });
});
