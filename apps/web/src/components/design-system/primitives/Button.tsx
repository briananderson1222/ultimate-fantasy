"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-blue-600 text-white shadow hover:bg-blue-700 focus-visible:ring-blue-500",
        secondary:
          "bg-gray-100 text-gray-900 shadow-sm hover:bg-gray-200 focus-visible:ring-gray-500",
        success: "bg-green-600 text-white shadow hover:bg-green-700 focus-visible:ring-green-500",
        warning: "bg-amber-500 text-white shadow hover:bg-amber-600 focus-visible:ring-amber-500",
        danger: "bg-red-600 text-white shadow hover:bg-red-700 focus-visible:ring-red-500",
        destructive: "bg-red-600 text-white shadow hover:bg-red-700 focus-visible:ring-red-500",
        outline:
          "border border-gray-300 bg-transparent text-gray-700 shadow-sm hover:bg-gray-50 hover:border-gray-400 focus-visible:ring-gray-500",
        ghost: "bg-transparent text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-500",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4",
        lg: "h-12 px-6 text-base",
        xl: "h-14 px-8 text-lg",
      },
      fullWidth: {
        true: "w-full",
        false: "",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      fullWidth: false,
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  isIconOnly?: boolean;
  children?: React.ReactNode;
}

// Simple icon component - in a real app you'd use a proper icon library
const Icon = ({ name, className }: { name: string; className?: string }) => {
  const iconMap: Record<string, string> = {
    plus: "+",
    refresh: "↻",
    trash: "🗑",
    "external-link": "↗",
    settings: "⚙",
    star: "★",
    "more-vertical": "⋮",
    filter: "⚡",
    loading: "⟳",
  };

  return <span className={cn("inline-block", className)}>{iconMap[name] || "?"}</span>;
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      loading = false,
      disabled,
      leftIcon,
      rightIcon,
      isIconOnly,
      children,
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    // Icon-only button
    if (isIconOnly) {
      return (
        <button
          className={cn(
            buttonVariants({ variant, size, fullWidth }),
            "aspect-square p-0",
            className,
          )}
          ref={ref}
          disabled={isDisabled}
          {...props}
        >
          {loading ? <Icon name="loading" className="animate-spin" /> : children}
        </button>
      );
    }

    return (
      <button
        className={cn(buttonVariants({ variant, size, fullWidth }), className)}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {loading && <Icon name="loading" className="animate-spin" />}
        {!loading && leftIcon && leftIcon}

        {children}

        {!loading && rightIcon && rightIcon}
      </button>
    );
  },
);

Button.displayName = "Button";

export { Button };
