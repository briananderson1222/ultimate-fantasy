"use client";

import React from "react";
import Link from "next/link";
import { useTheme } from "../app/theme";
import { Command, Settings, Moon, Sun } from "lucide-react";
import AdminPanel from "./AdminPanel";

export default function HeaderActions() {
  const { theme, setTheme } = useTheme();

  function toggleTheme() {
    setTheme(theme === "dark" ? "light" : "dark");
  }

  function openCommandPalette() {
    try {
      // Notify CommandPalette to open via a lightweight custom event
      window.dispatchEvent(new CustomEvent("uf:open-cmdk"));
    } catch {}
  }

  return (
    <div className="flex items-center gap-2">
      {/* Admin Panel (only in dev mode) */}
      <AdminPanel />

      {/* Command Palette */}
      <button
        type="button"
        onClick={openCommandPalette}
        className="inline-flex items-center justify-center rounded border border-[var(--border)] px-2 py-1 text-sm hover:bg-[var(--color-elevated)] focus-visible:ring-2 focus-visible:ring-offset-2"
        style={{ color: "var(--color-text)" }}
        aria-label="Open Command Palette (Ctrl/Cmd+K)"
        title="Command (Ctrl/Cmd+K)"
      >
        <Command className="h-4 w-4" aria-hidden />
      </button>

      {/* Theme toggle */}
      <button
        type="button"
        onClick={toggleTheme}
        className="inline-flex items-center justify-center rounded border border-[var(--border)] px-2 py-1 text-sm hover:bg-[var(--color-elevated)] focus-visible:ring-2 focus-visible:ring-offset-2"
        style={{ color: "var(--color-text)" }}
        aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        title={theme === "dark" ? "Light" : "Dark"}
      >
        {theme === "dark" ? (
          <Sun className="h-4 w-4" aria-hidden />
        ) : (
          <Moon className="h-4 w-4" aria-hidden />
        )}
      </button>

      {/* Settings */}
      <Link
        href="/settings/theme"
        className="inline-flex items-center justify-center rounded border border-[var(--border)] px-2 py-1 text-sm hover:bg-[var(--color-elevated)] focus-visible:ring-2 focus-visible:ring-offset-2"
        style={{ color: "var(--color-text)" }}
        aria-label="Theme Settings"
        title="Settings"
      >
        <Settings className="h-4 w-4" aria-hidden />
      </Link>
    </div>
  );
}
