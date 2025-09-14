"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { twMerge } from "tailwind-merge";
import clsx from "clsx";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-[var(--radius-md)] font-medium transition-all duration-[var(--anim-duration-xs)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)] disabled:opacity-60 disabled:cursor-not-allowed press-scale hover-lift",
  {
    variants: {
      variant: {
        primary: "bg-[var(--color-primary)] text-[var(--color-primary-contrast)] hover:opacity-90 active:opacity-95",
        secondary: "bg-[var(--color-secondary)] text-[var(--color-secondary-contrast)] hover:opacity-90 active:opacity-95",
        ghost: "bg-transparent text-[var(--color-text)] hover:bg-[rgba(0,0,0,0.04)] active:bg-[rgba(0,0,0,0.08)]",
      },
      size: {
        sm: "px-[var(--space-2)] py-[calc(var(--space-1))] text-sm",
        md: "px-[var(--space-3)] py-[var(--space-2)] text-sm",
        lg: "px-[var(--space-4)] py-[var(--space-3)] text-base",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    loading?: boolean;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
  };

export function Button({
  variant,
  size,
  loading = false,
  leftIcon,
  rightIcon,
  className,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Spinner = (
    <span
      aria-hidden
      className={clsx(
        "mr-2 inline-block h-4 w-4 loading-spinner rounded-full border-2",
        variant === "primary"
          ? "[border-color:rgba(255,255,255,0.3)] border-t-[var(--color-primary-contrast)]"
          : "[border-color:rgba(0,0,0,0.2)] border-t-[var(--color-text)]"
      )}
    />
  );

  return (
    <button
      className={twMerge(buttonVariants({ variant, size }), className)}
      aria-busy={loading || undefined}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          {Spinner}
          {children}
        </>
      ) : (
        <>
          {leftIcon && <span className="mr-2">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="ml-2">{rightIcon}</span>}
        </>
      )}
    </button>
  );
}
