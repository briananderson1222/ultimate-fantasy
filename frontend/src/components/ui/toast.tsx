"use client";

import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import * as ToastPr from "@radix-ui/react-toast";

type Toast = { id: string; title: string; description?: string };

type ToastContextValue = {
  toasts: Toast[];
  show: (t: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (t: Omit<Toast, "id">) => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev, { id, ...t }]);
      setTimeout(() => dismiss(id), 3000);
    },
    [dismiss]
  );

  const value = useMemo(() => ({ toasts, show, dismiss }), [toasts, show, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      <ToastPr.Provider swipeDirection="right">
        {children}
        {toasts.map((t) => (
          <ToastPr.Root
            key={t.id}
            duration={3000}
            className="uf-toast toast-enter min-w-[240px] rounded-lg border border-[var(--border)] bg-[var(--color-surface)] p-4 shadow-lg backdrop-blur-sm"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--border)',
              color: 'var(--color-text)',
              boxShadow: 'var(--shadow-md)'
            }}
            onOpenChange={(open) => {
              if (!open) dismiss(t.id);
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <ToastPr.Title className="font-medium text-[var(--color-text)]">{t.title}</ToastPr.Title>
                {t.description && (
                  <ToastPr.Description className="mt-1 text-sm text-[var(--color-muted)]">{t.description}</ToastPr.Description>
                )}
              </div>
              <ToastPr.Close 
                aria-label="Close notification" 
                className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--color-muted)] hover:bg-[var(--color-elevated)] hover:text-[var(--color-text)] focus-ring transition-colors"
              >
                ×
              </ToastPr.Close>
            </div>
          </ToastPr.Root>
        ))}
        <ToastPr.Viewport
          className="fixed bottom-4 right-4 z-50 flex max-h-[100vh] w-[360px] flex-col gap-2 outline-none"
          aria-live="polite"
        />
      </ToastPr.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
