import React from "react";

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={("rounded-[var(--radius-md)] border bg-[var(--color-surface)] p-4 shadow-sm transition-shadow hover:shadow-md " + (className || "")).trim()}
      style={{ borderColor: 'var(--border)', color: 'var(--color-text)' }}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={"mb-2 flex items-center justify-between " + (className || "")}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h2 className={"font-medium " + (className || "")}>{children}</h2>;
}
