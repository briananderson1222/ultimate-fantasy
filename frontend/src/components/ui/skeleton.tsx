"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { twMerge } from "tailwind-merge";

const skeletonVariants = cva("skeleton animate-shimmer", {
  variants: {
    variant: {
      text: "skeleton-text",
      avatar: "skeleton-avatar",
      button: "skeleton-button",
      card: "skeleton-card",
      custom: "",
    },
    width: {
      full: "w-full",
      "3/4": "w-3/4",
      "1/2": "w-1/2",
      "1/4": "w-1/4",
      auto: "w-auto",
    },
  },
  defaultVariants: {
    variant: "text",
    width: "full",
  },
});

type SkeletonProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof skeletonVariants> & {
    lines?: number;
    height?: string | number;
  };

export function Skeleton({
  variant,
  width,
  lines = 1,
  height,
  className,
  style,
  ...props
}: SkeletonProps) {
  if (variant === "text" && lines > 1) {
    return (
      <div className="space-y-2" {...props}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={twMerge(
              skeletonVariants({ variant, width: i === lines - 1 ? "3/4" : "full" }),
              className,
            )}
            style={{ height, ...style }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={twMerge(skeletonVariants({ variant, width }), className)}
      style={{ height, ...style }}
      {...props}
    />
  );
}

// Preset skeleton components
export function SkeletonCard({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={twMerge("space-y-3 p-4", className)} {...props}>
      <Skeleton variant="text" width="3/4" />
      <Skeleton variant="text" lines={2} />
      <div className="flex items-center space-x-2">
        <Skeleton variant="avatar" />
        <Skeleton variant="text" width="1/2" />
      </div>
    </div>
  );
}

export function SkeletonTable({
  rows = 5,
  cols = 4,
  className,
  ...props
}: {
  rows?: number;
  cols?: number;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={twMerge("space-y-2", className)} {...props}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex space-x-4">
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} variant="text" width={j === 0 ? "1/4" : "auto"} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonList({
  items = 3,
  className,
  ...props
}: {
  items?: number;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={twMerge("space-y-4", className)} {...props}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-3">
          <Skeleton variant="avatar" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" width="3/4" />
            <Skeleton variant="text" width="1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}
