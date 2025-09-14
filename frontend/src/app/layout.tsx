import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import { Trophy, Menu as MenuIcon } from "lucide-react";
import I18nNav from "../components/I18nNav";
import LocaleSwitcher from "../components/LocaleSwitcher";
import HeaderActions from "../components/HeaderActions";
import LeagueSwitcher from "../components/LeagueSwitcher";
import Logo from "../components/Logo";

export const metadata: Metadata = {
  title: "Ultimate Fantasy Platform",
  description: "Fantasy sports platform frontend",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:m-2 focus:rounded focus:bg-white focus:px-3 focus:py-1 focus:shadow">Skip to content</a>
        <Providers>
        <header className="border-b bg-[var(--color-surface)]" style={{ borderColor: 'var(--border)', color: 'var(--color-text)' }}>
          <div className="mx-auto flex max-w-6xl items-center justify-between p-3 md:p-4">
            <a href="/" className="flex items-center gap-2 font-semibold hover:opacity-90">
              {/* Prefer brand logo if present; fall back to icon + text */}
              <Logo />
              <span className="inline-flex items-center gap-2 md:hidden">
                <Trophy className="h-5 w-5" aria-hidden />
                <span>Ultimate Fantasy</span>
              </span>
            </a>

            {/* Desktop nav (i18n) */}
            <I18nNav />

            {/* Right side actions */}
            <div className="flex items-center gap-2 md:gap-3">
              {/* League switcher */}
              <div className="hidden md:block">
                <LeagueSwitcher />
              </div>
              {/* Locale switcher */}
              <div className="hidden md:block">
                <LocaleSwitcher />
              </div>
              <HeaderActions />
              {/* Mobile menu (no JS, native details/summary) */}
              <details className="md:hidden">
                <summary className="cursor-pointer rounded border px-2 py-1 text-sm inline-flex items-center gap-2">
                  <MenuIcon className="h-5 w-5" aria-hidden />
                  <span>Menu</span>
                </summary>
                {/* Mobile nav and items rendered via I18nNav as well */}
                <div className="space-y-2 py-2">
                  <div className="px-2"><LeagueSwitcher /></div>
                  <I18nNav />
                </div>
              </details>
            </div>
          </div>
        </header>
          <main id="main">
            <div className="mx-auto max-w-6xl p-3 md:p-4">{children}</div>
          </main>
        <footer className="border-t bg-[var(--color-surface)]" style={{ borderColor: 'var(--border)', color: 'var(--color-muted)' }}>
          <div className="mx-auto max-w-6xl p-4 text-xs">
            <div className="flex flex-col items-start justify-between gap-2 md:flex-row md:items-center">
              <div>© {new Date().getFullYear()} Ultimate Fantasy</div>
              <nav className="flex flex-wrap items-center gap-3">
                <a className="underline-offset-2 hover:underline" href="/settings/theme">Theme</a>
                <a className="underline-offset-2 hover:underline" href="/leagues">Leagues</a>
                <a className="underline-offset-2 hover:underline" href="/dashboard">Dashboard</a>
              </nav>
            </div>
          </div>
        </footer>
        </Providers>
      </body>
    </html>
  );
}
