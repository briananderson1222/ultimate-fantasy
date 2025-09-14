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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const raw = localStorage.getItem('uf_theme');
                  const theme = raw ? JSON.parse(raw) : 'dark';
                  document.documentElement.setAttribute('data-theme', theme);
                } catch (e) {
                  document.documentElement.setAttribute('data-theme', 'dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className="bg-[var(--color-bg)] text-[var(--color-text)]">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:m-2 focus:rounded focus:bg-white focus:px-3 focus:py-1 focus:shadow"
        >
          Skip to content
        </a>
        <Providers>
          <header
            className="border-b bg-[var(--color-surface)]"
            style={{ borderColor: "var(--border)", color: "var(--color-text)" }}
          >
            <div className="mx-auto flex max-w-6xl items-center justify-between p-3 md:p-4">
              <a href="/" className="flex items-center gap-2 font-semibold hover:opacity-90">
                <Logo />
              </a>

              {/* Desktop nav */}
              <div className="hidden md:block">
                <I18nNav />
              </div>

              {/* Right side actions */}
              <div className="flex items-center gap-2">
                {/* Desktop controls */}
                <div className="hidden md:flex items-center gap-2">
                  <LeagueSwitcher />
                  <LocaleSwitcher />
                </div>

                {/* Always visible actions */}
                <HeaderActions />

                {/* Mobile menu */}
                <details className="md:hidden relative">
                  <summary className="cursor-pointer rounded border border-[var(--border)] bg-[var(--color-surface)] px-2 py-1 text-sm inline-flex items-center gap-1 hover:bg-[var(--color-elevated)]">
                    <MenuIcon className="h-4 w-4" aria-hidden />
                    <span className="sr-only">Menu</span>
                  </summary>
                  <div className="absolute right-0 top-full mt-1 w-48 bg-[var(--color-surface)] border border-[var(--border)] rounded-lg shadow-lg p-2 space-y-2 z-50">
                    <div className="border-b border-[var(--border)] pb-2 mb-2">
                      <LeagueSwitcher />
                    </div>
                    <div className="border-b border-[var(--border)] pb-2 mb-2">
                      <LocaleSwitcher />
                    </div>
                    <I18nNav />
                  </div>
                </details>
              </div>
            </div>
          </header>
          <main id="main">
            <div className="mx-auto max-w-6xl p-3 md:p-4">{children}</div>
          </main>
          <footer
            className="border-t bg-[var(--color-surface)]"
            style={{ borderColor: "var(--border)", color: "var(--color-muted)" }}
          >
            <div className="mx-auto max-w-6xl p-4 text-xs">
              <div className="flex flex-col items-start justify-between gap-2 md:flex-row md:items-center">
                <div>© {new Date().getFullYear()} Ultimate Fantasy</div>
                <nav className="flex flex-wrap items-center gap-3">
                  <a className="underline-offset-2 hover:underline" href="/settings/theme">
                    Theme
                  </a>
                  <a className="underline-offset-2 hover:underline" href="/leagues">
                    Leagues
                  </a>
                  <a className="underline-offset-2 hover:underline" href="/dashboard">
                    Dashboard
                  </a>
                </nav>
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
