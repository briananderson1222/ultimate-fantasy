"use client";

import clsx from "clsx";
import React from "react";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  error?: string;
  label?: string;
};

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ error, label, className, id, ...props }, ref) => {
    const inputId = id || props.name || Math.random().toString(36).slice(2);
    const describedById = error ? `${inputId}-error` : undefined;
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="block text-sm text-[var(--color-muted)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            "w-full rounded-[var(--radius-md)] border px-[var(--space-3)] py-[var(--space-2)] transition-all duration-[var(--anim-duration-xs)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)] hover:border-[var(--color-muted)]",
            error ? "border-red-500 focus:border-red-500" : "border-[var(--border)] focus:border-[var(--ring)]",
            className
          )}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedById}
          {...props}
        />
        {error && (
          <p id={describedById} className="animate-slide-up text-xs text-red-600">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
