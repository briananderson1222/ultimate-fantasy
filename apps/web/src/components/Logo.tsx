"use client";

import React from "react";

export default function Logo({
  size = "md",
  className = "",
}: {
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const sizeClasses = {
    sm: "h-6 w-6 text-sm",
    md: "h-8 w-8 text-base",
    lg: "h-12 w-12 text-xl",
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`${sizeClasses[size]} bg-[var(--color-primary)] rounded-md flex items-center justify-center font-bold text-[var(--color-primary-contrast)]`}
      >
        UF
      </div>
      <span className="font-bold text-[var(--color-text)] tracking-wide">ULTIMATE FANTASY</span>
    </div>
  );
}
