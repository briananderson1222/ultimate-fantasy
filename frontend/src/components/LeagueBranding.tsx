"use client";

import React from "react";

type Vars = Record<string, string>;

export function LeagueBranding({
  themeVars,
  children,
}: {
  themeVars?: Vars;
  children: React.ReactNode;
}) {
  if (!themeVars || Object.keys(themeVars).length === 0) return <>{children}</>;
  // Apply provided CSS variables to a wrapping element to override theme locally
  const style = themeVars as React.CSSProperties & Record<string, string>;
  return (
    <div style={style} data-league-branding>
      {children}
    </div>
  );
}
