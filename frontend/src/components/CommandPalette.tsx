"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Modal } from "./ui/modal";
import { useI18n } from "../app/i18n";

type Command = {
  id: string;
  title: string;
  hint?: string;
  keywords?: string[];
  shortcut?: string; // for display only
  run: () => void;
};

export default function CommandPalette() {
  const router = useRouter();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const commands: Command[] = useMemo(
    () => [
      {
        id: "go-dashboard",
        title: t("nav.dashboard"),
        hint: "Go to dashboard",
        keywords: ["home", "widgets"],
        shortcut: "G D",
        run: () => router.push("/dashboard"),
      },
      {
        id: "go-leagues",
        title: t("nav.leagues"),
        hint: "View my leagues",
        keywords: ["teams", "list"],
        shortcut: "G L",
        run: () => router.push("/leagues"),
      },
      {
        id: "create-league",
        title: "Create League",
        hint: "Start a new league",
        keywords: ["new", "league", "create"],
        shortcut: "⇧⌘C",
        run: () => router.push("/leagues/create"),
      },
      {
        id: "join-league",
        title: "Join League",
        hint: "Join by League ID",
        keywords: ["join", "league"],
        shortcut: "⇧⌘J",
        run: () => {
          const id = window.prompt("Enter League ID (UUID)");
          if (id) router.push(`/leagues/${id}`);
        },
      },
      {
        id: "set-lineup",
        title: t("pages.lineup.title"),
        hint: "Manage your lineup",
        keywords: ["lineup", "players", "set"],
        shortcut: "⇧⌘L",
        run: () => router.push("/lineup"),
      },
      {
        id: "waivers",
        title: t("pages.waivers.title"),
        hint: "Place bids and view activity",
        keywords: ["waivers", "bids"],
        run: () => router.push("/waivers"),
      },
      {
        id: "theme-settings",
        title: "Theme Settings",
        hint: "Customize colors and tokens",
        keywords: ["theme", "settings", "design"],
        run: () => router.push("/settings/theme"),
      },
    ],
    [router, t]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) => {
      const inTitle = c.title.toLowerCase().includes(q);
      const inKeywords = (c.keywords || []).some((k) => k.toLowerCase().includes(q));
      return inTitle || inKeywords;
    });
  }, [commands, query]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isMeta = e.ctrlKey || e.metaKey;
      if (isMeta && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
        return;
      }
      if (isMeta && e.shiftKey && e.key.toLowerCase() === "c") {
        e.preventDefault();
        router.push("/leagues/create");
        return;
      }
      if (isMeta && e.shiftKey && e.key.toLowerCase() === "l") {
        e.preventDefault();
        router.push("/lineup");
        return;
      }
      if (isMeta && e.shiftKey && e.key.toLowerCase() === "j") {
        e.preventDefault();
        const id = window.prompt("Enter League ID (UUID)");
        if (id) router.push(`/leagues/${id}`);
        return;
      }
    }
    function onOpenEvent() {
      setOpen(true);
    }
    window.addEventListener("keydown", onKey);
    window.addEventListener("uf:open-cmdk" as any, onOpenEvent as any);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("uf:open-cmdk" as any, onOpenEvent as any);
    };
  }, [router]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setQuery("");
      setIndex(0);
    }
  }, [open]);

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIndex((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIndex((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      filtered[index]?.run();
      setOpen(false);
    }
  }

  return (
    <Modal open={open} onClose={() => setOpen(false)} title="Command Palette">
      <div className="space-y-2">
        <div className="rounded border bg-white p-2">
          <label className="sr-only" htmlFor="cmdk-input">
            Search commands
          </label>
          <input
            id="cmdk-input"
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search (type or use ↑/↓ to navigate, Enter to run)"
            className="w-full rounded px-2 py-2 outline-none"
          />
        </div>
        <ul role="listbox" aria-label="Commands" className="max-h-80 overflow-auto rounded border">
          {filtered.length === 0 && (
            <li className="px-3 py-2 text-sm text-gray-600">No commands</li>
          )}
          {filtered.map((c, i) => (
            <li
              key={c.id}
              role="option"
              aria-selected={i === index}
              className={`flex items-center justify-between px-3 py-2 text-sm ${
                i === index ? "bg-gray-100" : ""
              }`}
              onMouseEnter={() => setIndex(i)}
              onClick={() => {
                c.run();
                setOpen(false);
              }}
            >
              <div>
                <div className="font-medium">{c.title}</div>
                {c.hint && <div className="text-xs text-gray-600">{c.hint}</div>}
              </div>
              {c.shortcut && (
                <div className="text-xs text-gray-500 border rounded px-1 py-0.5">{c.shortcut}</div>
              )}
            </li>
          ))}
        </ul>
        <div className="text-xs text-gray-600">Shortcut: Cmd/Ctrl + K</div>
      </div>
    </Modal>
  );
}
