import { render, screen } from "@testing-library/react";
import React from "react";

// Mock react-query's useQuery to avoid needing a provider and network
import * as RQ from "@tanstack/react-query";
vi.spyOn(RQ, "useQuery").mockImplementation(
  () =>
    ({
      isLoading: false,
      isError: false,
      data: { items: [] },
      error: undefined as any,
      refetch: vi.fn(),
    }) as any,
);

import LeaguesListPage from "../../src/app/leagues/page";

describe("LeaguesListPage", () => {
  it("renders the page header", () => {
    render(<LeaguesListPage />);
    expect(screen.getByRole("heading", { name: /leagues/i })).toBeInTheDocument();
  });
});
