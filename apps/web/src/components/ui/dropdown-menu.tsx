import React from "react";

export interface DropdownMenuProps {
  children?: React.ReactNode;
}

export const DropdownMenu = ({ children }: DropdownMenuProps) => (
  <div className="relative inline-block text-left">{children}</div>
);

export const DropdownMenuTrigger = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => <div className={className}>{children}</div>;

export const DropdownMenuContent = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div
    className={`absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none ${className || ""}`}
  >
    <div className="py-1">{children}</div>
  </div>
);

export const DropdownMenuItem = ({
  children,
  className,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}) => (
  <div
    className={`block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 cursor-pointer ${className || ""}`}
    onClick={onClick}
  >
    {children}
  </div>
);
