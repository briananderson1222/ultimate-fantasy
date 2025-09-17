"use client";

import clsx from "clsx";
import React from "react";

type BadgeProps = {
  children: React.ReactNode;
  variant?: "default" | "secondary" | "success" | "warning" | "destructive";
  className?: string;
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  const base = "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium";
  const variants = {
    default: "bg-[var(--color-surface)] text-[var(--color-text)] border border-[var(--border)]",
    secondary: "bg-[var(--color-elevated)] text-[var(--color-muted)]",
    success: "bg-green-100 text-green-800 border border-green-200",
    warning: "bg-yellow-100 text-yellow-800 border border-yellow-200",
    destructive: "bg-red-100 text-red-800 border border-red-200",
  } as const;
  return <span className={clsx(base, variants[variant], className)}>{children}</span>;
}
