import React from "react";
import { render, screen } from "@testing-library/react";
import CommandPalette from "../../src/components/CommandPalette";

// Mock i18n context
vi.mock("../../src/app/i18n", () => ({
  useI18n: () => ({
    t: (k: string) => k.split(".").pop(),
    locale: "en-US",
    setLocale: vi.fn(),
    messages: {},
  }),
}));

// Mock next/navigation useRouter
const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

describe("CommandPalette", () => {
  it("opens on Ctrl+K and renders input", () => {
    render(<CommandPalette />);
    const event = new KeyboardEvent("keydown", { key: "k", ctrlKey: true });
    window.dispatchEvent(event);
    expect(screen.getByPlaceholderText(/Search \(type or use/)).toBeInTheDocument();
  });
});
