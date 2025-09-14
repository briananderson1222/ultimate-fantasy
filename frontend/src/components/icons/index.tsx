"use client";

import * as React from "react";
import type { SVGProps } from "react";

// Custom football icons (inline SVGs). Keep size/role consistent.
export function FootballBall(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden focusable="false" {...props}>
      <path fill="currentColor" d="M3.7 12.7c-1.9-1.9-.9-4.9 1.5-7.3S11.1 1.9 13 3.8l7.3 7.3c1.9 1.9.9 4.9-1.5 7.3s-5.4 3.4-7.3 1.5L3.7 12.7z"/>
      <path stroke="#fff" strokeWidth="1.5" strokeLinecap="round" d="M8 12h8M12 10v4"/>
    </svg>
  );
}

export function FootballField(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden focusable="false" {...props}>
      <rect x="3" y="5" width="18" height="14" rx="2" ry="2" fill="none" stroke="currentColor" strokeWidth="1.5"/>
      <path stroke="currentColor" strokeWidth="1" d="M12 5v14M7 5v14M17 5v14"/>
      <path stroke="currentColor" strokeWidth="0.8" d="M3 9h18M3 15h18"/>
    </svg>
  );
}

export function GoalPosts(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden focusable="false" {...props}>
      <path stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" d="M6 4v6M18 4v6M6 10h12M12 10v9M9 19h6"/>
    </svg>
  );
}

export function Helmet(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden focusable="false" {...props}>
      <path fill="none" stroke="currentColor" strokeWidth="1.5" d="M20 12a8 8 0 1 0-16 0v2a2 2 0 0 0 2 2h5v3h3l2-3h2a2 2 0 0 0 2-2v-2z"/>
      <circle cx="9" cy="12" r="1.5" fill="currentColor"/>
    </svg>
  );
}

// Wrapper component for consistent sizing and a11y naming
export type IconProps = {
  title?: string;
  size?: number | string;
  className?: string;
  color?: string;
  children: React.ReactElement<SVGProps<SVGSVGElement>>;
};

export function Icon({ title, size = 16, className, color, children }: IconProps) {
  const child = React.cloneElement(children, {
    className,
    width: typeof size === "number" ? `${size}` : size,
    height: typeof size === "number" ? `${size}` : size,
    role: title ? "img" : undefined,
    "aria-label": title || undefined,
    "aria-hidden": title ? undefined : true,
    style: { color, ...(children.props.style || {}) },
  });
  return child;
}

export type IconName =
  | "football-ball"
  | "football-field"
  | "goal-posts"
  | "helmet";

export const ICONS: Record<IconName, (props?: Partial<IconProps>) => React.JSX.Element> = {
  "football-ball": (p) => (
    <Icon {...p}>
      <FootballBall />
    </Icon>
  ),
  "football-field": (p) => (
    <Icon {...p}>
      <FootballField />
    </Icon>
  ),
  "goal-posts": (p) => (
    <Icon {...p}>
      <GoalPosts />
    </Icon>
  ),
  helmet: (p) => (
    <Icon {...p}>
      <Helmet />
    </Icon>
  ),
};

