import React from "react";

export interface PopoverProps {
  children?: React.ReactNode;
}

export const Popover = ({ children }: PopoverProps) => <div className="relative">{children}</div>;

export const PopoverTrigger = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => <div className={className}>{children}</div>;

export const PopoverContent = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div className={`absolute z-10 w-72 rounded-md border bg-white p-4 shadow-md ${className || ""}`}>
    {children}
  </div>
);
