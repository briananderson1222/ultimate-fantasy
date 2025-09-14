import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";

// Mock router
const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// Mock react-query useMutation to avoid provider and network
const mutate = vi.fn();
vi.mock("@tanstack/react-query", async (orig) => {
  return {
    ...(await orig()),
    useMutation: () => ({ mutate, isPending: false, isError: false, error: undefined }),
  };
});

import CreateLeaguePage from "../../src/app/leagues/create/page";
import { ToastProvider } from "../../src/components/ui/toast";

describe("CreateLeaguePage form validation", () => {
  beforeEach(() => {
    mutate.mockReset();
    push.mockReset();
  });

  it("shows validation messages on invalid submit", async () => {
    render(
      <ToastProvider>
        <CreateLeaguePage />
      </ToastProvider>,
    );

    // Clear default values to force validation errors
    const name = screen.getByLabelText("Name");
    fireEvent.change(name, { target: { value: "A" } });

    const season = screen.getByLabelText("Season");
    fireEvent.change(season, { target: { value: "20" } });

    const submit = screen.getByRole("button", { name: /create/i });
    fireEvent.click(submit);

    await screen.findByText(/at least 2 characters|must be at least 2/i);
    await screen.findByText(/4-digit year/i);
    expect(mutate).not.toHaveBeenCalled();
  });

  it("submits valid form", async () => {
    render(
      <ToastProvider>
        <CreateLeaguePage />
      </ToastProvider>,
    );

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "My Test League" } });
    fireEvent.change(screen.getByLabelText("Sport"), { target: { value: "nba" } });
    fireEvent.change(screen.getByLabelText("League Type"), { target: { value: "redraft" } });
    fireEvent.change(screen.getByLabelText("Season"), { target: { value: "2025" } });

    fireEvent.click(screen.getByRole("button", { name: /create/i }));
    expect(mutate).toHaveBeenCalled();
  });
});
