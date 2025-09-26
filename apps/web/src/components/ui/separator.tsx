import React from "react";

export interface SeparatorProps {
  className?: string;
  orientation?: "horizontal" | "vertical";
}

export const Separator = ({ className, orientation = "horizontal" }: SeparatorProps) => (
  <div
    className={`shrink-0 bg-gray-200 ${
      orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]"
    } ${className || ""}`}
  />
);
