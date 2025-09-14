import { act, render, screen } from "@testing-library/react";
import React from "react";
import { ToastProvider, useToast } from "../../src/components/ui/toast";

function Demo() {
  const toast = useToast();
  return (
    <button onClick={() => toast.show({ title: "Saved", description: "It worked" })}>Show</button>
  );
}

describe("Toast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("auto-dismisses after 3 seconds", () => {
    render(
      <ToastProvider>
        <Demo />
      </ToastProvider>,
    );

    screen.getByRole("button", { name: /show/i }).click();

    // Toast appears
    screen.getByText("Saved");
    // Advance timers
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    // Toast disappears
    expect(screen.queryByText("Saved")).toBeNull();
  });
});
