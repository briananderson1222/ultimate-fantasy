"use client";

import React from "react";
import { twMerge } from "tailwind-merge";

type EmptyStateProps = {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={twMerge(
      "empty-state-fade flex flex-col items-center justify-center py-12 px-4 text-center",
      className
    )}>
      {icon && (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-elevated)] text-[var(--color-muted)] animate-scale-in">
          {icon}
        </div>
      )}
      <h3 className="mb-2 text-lg font-medium text-[var(--color-text)] animate-fade-in" style={{ animationDelay: 'var(--anim-delay-xs)' }}>
        {title}
      </h3>
      {description && (
        <p className="mb-6 max-w-sm text-[var(--color-muted)] animate-fade-in" style={{ animationDelay: 'var(--anim-delay-sm)' }}>
          {description}
        </p>
      )}
      {action && (
        <div className="animate-fade-in" style={{ animationDelay: 'var(--anim-delay-md)' }}>
          {action}
        </div>
      )}
    </div>
  );
}
