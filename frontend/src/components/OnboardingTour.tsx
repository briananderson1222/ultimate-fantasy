"use client";

import React, { useEffect, useMemo, useState } from "react";

type Step = {
  selector: string;
  title: string;
  content: string;
};

export default function OnboardingTour({
  id,
  steps,
  open,
  onClose,
}: {
  id: string;
  steps: Step[];
  open: boolean;
  onClose: () => void;
}) {
  const storageKey = `uf_tour_completed:${id}`;
  const [idx, setIdx] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);

  const completed = useMemo(() => {
    try {
      return localStorage.getItem(storageKey) === "1";
    } catch {
      return false;
    }
  }, [storageKey]);

  useEffect(() => {
    if (!open) return;
    function compute() {
      const step = steps[idx];
      if (!step) return;
      const el = document.querySelector(step.selector) as HTMLElement | null;
      if (el) {
        const r = el.getBoundingClientRect();
        setRect(r);
      } else {
        setRect(null);
      }
    }
    compute();
    const handler = () => compute();
    window.addEventListener("resize", handler);
    window.addEventListener("scroll", handler, true);
    return () => {
      window.removeEventListener("resize", handler);
      window.removeEventListener("scroll", handler, true);
    };
  }, [open, idx, steps]);

  if (!open || completed) return null;
  const step = steps[idx];
  if (!step) return null;

  function finish() {
    try {
      localStorage.setItem(storageKey, "1");
    } catch {}
    onClose();
  }

  const pad = 8;
  const highlightStyle: React.CSSProperties = rect
    ? {
        position: "fixed",
        top: Math.max(0, rect.top - pad),
        left: Math.max(0, rect.left - pad),
        width: rect.width + pad * 2,
        height: rect.height + pad * 2,
        border: "2px solid #ffffff",
        borderRadius: 6,
        boxShadow: "0 0 0 9999px rgba(0,0,0,0.4)",
        pointerEvents: "none",
      }
    : { display: "none" };

  // Tooltip positioning
  const tooltipStyle: React.CSSProperties = rect
    ? {
        position: "fixed",
        top: Math.min(window.innerHeight - 140, rect.bottom + 10),
        left: Math.max(10, Math.min(window.innerWidth - 360, rect.left)),
        width: 340,
        zIndex: 100000,
      }
    : {
        position: "fixed",
        top: 80,
        left: 20,
        width: 340,
        zIndex: 100000,
      };

  return (
    <div aria-live="polite">
      {/* Overlay mask */}
      <div
        className="fixed inset-0 z-[99999]"
        onClick={() => setIdx((i) => Math.min(steps.length - 1, i + 1))}
        aria-hidden
      />
      {/* Highlight */}
      <div style={highlightStyle} className="z-[100000] rounded" aria-hidden />
      {/* Tooltip */}
      <div style={tooltipStyle} role="dialog" aria-label="Onboarding step">
        <div className="rounded border bg-white p-3 shadow-lg">
          <div className="mb-1 text-sm font-medium">{step.title}</div>
          <div className="mb-2 text-sm text-gray-700">{step.content}</div>
          <div className="flex items-center justify-between text-sm">
            <div className="text-xs text-gray-600">
              Step {idx + 1} of {steps.length}
            </div>
            <div className="flex items-center gap-2">
              <button
                className="rounded bg-gray-100 px-2 py-1"
                onClick={() => (idx > 0 ? setIdx((i) => i - 1) : onClose())}
              >
                Back
              </button>
              {idx < steps.length - 1 ? (
                <button
                  className="rounded bg-blue-600 px-3 py-1 text-white"
                  onClick={() => setIdx((i) => Math.min(steps.length - 1, i + 1))}
                >
                  Next
                </button>
              ) : (
                <button
                  className="rounded bg-green-600 px-3 py-1 text-white"
                  onClick={finish}
                >
                  Done
                </button>
              )}
              <button
                className="rounded bg-gray-200 px-2 py-1"
                onClick={finish}
              >
                Skip
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

