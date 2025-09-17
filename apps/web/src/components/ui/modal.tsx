"use client";

import React from "react";
import * as Dialog from "@radix-ui/react-dialog";

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-[var(--color-overlay)]" />
        <Dialog.Content
          aria-modal="true"
          className="fixed left-1/2 top-1/2 z-50 w-[95vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-md)] bg-[var(--color-surface)] p-4 shadow-lg outline-none"
          style={{ color: "var(--color-text)", borderColor: "var(--border)" }}
        >
          <Dialog.Title className={title ? "mb-2 text-lg font-medium" : "sr-only"}>
            {title || "Modal"}
          </Dialog.Title>
          {children}
          <Dialog.Close
            aria-label="Close"
            className="absolute right-2 top-2 rounded-[var(--radius-sm)] px-2 py-1 text-xs text-[var(--color-muted)] hover:bg-[rgba(0,0,0,0.04)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)]"
          >
            Close (Esc)
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
