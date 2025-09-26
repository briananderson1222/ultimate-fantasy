"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../../lib/utils";

const progressBarVariants = cva("relative overflow-hidden bg-gray-200 dark:bg-gray-700", {
  variants: {
    variant: {
      default: "",
      success: "",
      warning: "",
      danger: "",
      error: "",
    },
    size: {
      sm: "h-2",
      md: "h-3",
      lg: "h-4",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "md",
  },
});

const progressFillVariants = cva("h-full transition-all duration-500 ease-out", {
  variants: {
    variant: {
      default: "bg-blue-600",
      success: "bg-green-600",
      warning: "bg-amber-500",
      danger: "bg-red-600",
      error: "bg-red-600",
    },
    animated: {
      true: "animate-pulse",
      false: "",
    },
  },
  defaultVariants: {
    variant: "default",
    animated: false,
  },
});

export interface ProgressBarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof progressBarVariants> {
  value: number;
  max?: number;
  showLabel?: boolean;
  label?: string;
  animated?: boolean;
}

const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
  (
    {
      className,
      variant,
      size,
      value,
      max = 100,
      showLabel = false,
      label,
      animated = false,
      ...props
    },
    ref,
  ) => {
    // Ensure value is within bounds
    const clampedValue = Math.min(Math.max(value, 0), max);
    const percentage = (clampedValue / max) * 100;

    // Determine variant based on value if not explicitly set
    const effectiveVariant = variant || getVariantFromValue(percentage);

    const displayLabel = label || (showLabel ? `${Math.round(percentage)}%` : "");

    return (
      <div className="space-y-2">
        {displayLabel && (
          <div className="flex justify-between items-center text-sm">
            <span className="font-medium text-gray-700 dark:text-gray-300">{displayLabel}</span>
            {showLabel && !label && (
              <span className="text-gray-500 dark:text-gray-400">
                {clampedValue}/{max}
              </span>
            )}
          </div>
        )}

        <div
          ref={ref}
          className={cn(
            progressBarVariants({ variant: effectiveVariant, size }),
            "rounded-full",
            className,
          )}
          role="progressbar"
          aria-valuenow={clampedValue}
          aria-valuemin={0}
          aria-valuemax={max}
          aria-label={displayLabel || `Progress: ${percentage.toFixed(1)}%`}
          {...props}
        >
          <div
            className={cn(
              progressFillVariants({ variant: effectiveVariant, animated }),
              "rounded-full transition-transform duration-500 ease-out",
            )}
            style={{
              width: `${percentage}%`,
              transform: animated ? "translateX(-100%)" : "translateX(0)",
              animation: animated ? "progressSlide 2s ease-out infinite" : undefined,
            }}
          />

          {/* Subtle shine effect for enhanced visual appeal */}
          <div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full"
            style={{
              width: `${percentage}%`,
              animation: animated ? "progressShine 2s ease-out infinite" : undefined,
            }}
          />
        </div>
      </div>
    );
  },
);

ProgressBar.displayName = "ProgressBar";

// Helper function to determine variant based on value
function getVariantFromValue(percentage: number): "success" | "warning" | "danger" | "default" {
  if (percentage >= 80) return "success";
  if (percentage >= 60) return "default";
  if (percentage >= 30) return "warning";
  return "danger";
}

export { ProgressBar };
