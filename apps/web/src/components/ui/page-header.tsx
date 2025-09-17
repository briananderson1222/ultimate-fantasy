"use client";

import React from "react";

export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={(
        "mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between " +
        (className || "")
      ).trim()}
    >
      <div>
        <h1 className="text-2xl font-semibold leading-tight">{title}</h1>
        {description && <p className="text-sm text-gray-600">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
