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
    default: "bg-gray-200 text-gray-900",
    secondary: "bg-gray-100 text-gray-700",
    success: "bg-green-100 text-green-800",
    warning: "bg-yellow-100 text-yellow-800",
    destructive: "bg-red-100 text-red-800",
  } as const;
  return <span className={clsx(base, variants[variant], className)}>{children}</span>;
}

