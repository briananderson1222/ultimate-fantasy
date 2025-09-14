"use client";

import React, { useId, useRef } from "react";

export function Tabs({
  tabs,
  value,
  onChange,
}: {
  tabs: { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  const id = useId();
  const btnRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    const current = tabs.findIndex((t) => t.value === value);
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      const delta = e.key === "ArrowRight" ? 1 : -1;
      const next = (current + delta + tabs.length) % tabs.length;
      const nextVal = tabs[next]?.value;
      if (nextVal) {
        onChange(nextVal);
        // Move focus to the new tab after state updates
        setTimeout(() => btnRefs.current[next]?.focus(), 0);
      }
    }
  }

  return (
    <div className="border-b mb-3" style={{ borderColor: 'var(--border)' }}>
      <nav
        className="-mb-px flex gap-2"
        aria-label="Tabs"
        role="tablist"
        aria-orientation="horizontal"
        onKeyDown={onKeyDown}
      >
        {tabs.map((t) => (
          <button
            key={t.value}
            className={
              "px-[var(--space-3)] py-[var(--space-2)] text-sm border-b-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)] " +
              (value === t.value
                ? "[border-bottom-color:var(--color-primary)] text-[var(--color-primary)]"
                : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)] hover:[border-bottom-color:var(--border)]")
            }
            onClick={() => onChange(t.value)}
            role="tab"
            aria-selected={value === t.value}
            tabIndex={value === t.value ? 0 : -1}
            ref={(el) => { btnRefs.current[tabs.findIndex((x) => x.value === t.value)] = el; }}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
