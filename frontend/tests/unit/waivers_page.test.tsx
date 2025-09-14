import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

// Mock react-query hooks to avoid needing a provider or network
vi.mock("@tanstack/react-query", async () => {
  const original = await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...original,
    useQuery: () => ({
      isLoading: false,
      isError: false,
      data: undefined,
      error: undefined,
      refetch: vi.fn(),
    }),
    useMutation: () => ({ mutate: vi.fn(), isPending: false, isError: false, error: undefined }),
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
      cancelQueries: vi.fn(),
      getQueryData: vi.fn(),
      setQueryData: vi.fn(),
    }),
  } as any;
});

import WaiversPage from "../../src/app/waivers/page";
import { ToastProvider } from "../../src/components/ui/toast";

describe("WaiversPage basic behavior", () => {
  it("disables Place Bid until required fields are filled", () => {
    render(
      <ToastProvider>
        <WaiversPage />
      </ToastProvider>,
    );

    // Heading renders
    expect(screen.getByRole("heading", { name: /waivers/i })).toBeInTheDocument();

    const btn = screen.getByRole("button", { name: /place bid/i });
    expect(btn).toBeDisabled();

    // Fill required inputs
    fireEvent.change(screen.getByLabelText("League ID"), { target: { value: "L1" } });
    fireEvent.change(screen.getByLabelText("Team ID"), { target: { value: "T1" } });
    fireEvent.change(screen.getByLabelText("Player ID"), { target: { value: "P1" } });
    fireEvent.change(screen.getByLabelText("Bid"), { target: { value: "10" } });

    expect(btn).not.toBeDisabled();
  });
});
