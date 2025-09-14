"use client";

import React from "react";
import { Home, Trophy, LayoutDashboard } from "lucide-react";
import { useI18n } from "../app/i18n";

export default function I18nNav() {
  const { t } = useI18n();
  return (
    <>
      <nav aria-label="Main" className="hidden md:block">
        <ul className="flex gap-4 text-sm">
          <li>
            <a
              className="inline-flex items-center gap-1 px-3 py-2 rounded min-h-12 hover:underline focus-visible:ring-2 focus-visible:ring-offset-2"
              href="/"
            >
              <Home className="h-4 w-4" aria-hidden />
              <span>{t("nav.home")}</span>
            </a>
          </li>
          <li>
            <a
              className="inline-flex items-center gap-1 px-3 py-2 rounded min-h-12 hover:underline focus-visible:ring-2 focus-visible:ring-offset-2"
              href="/leagues"
            >
              <Trophy className="h-4 w-4" aria-hidden />
              <span>{t("nav.leagues")}</span>
            </a>
          </li>
          <li>
            <a
              className="inline-flex items-center gap-1 px-3 py-2 rounded min-h-12 hover:underline focus-visible:ring-2 focus-visible:ring-offset-2"
              href="/dashboard"
            >
              <LayoutDashboard className="h-4 w-4" aria-hidden />
              <span>{t("nav.dashboard")}</span>
            </a>
          </li>
        </ul>
      </nav>

      <nav aria-label="Mobile" className="mt-2 md:hidden">
        <ul className="flex flex-col gap-2 text-sm">
          <li>
            <a
              className="flex items-center gap-2 rounded px-3 py-2 min-h-12 hover:bg-gray-100"
              href="/"
            >
              <Home className="h-4 w-4" aria-hidden />
              <span>{t("nav.home")}</span>
            </a>
          </li>
          <li>
            <a
              className="flex items-center gap-2 rounded px-3 py-2 min-h-12 hover:bg-gray-100"
              href="/leagues"
            >
              <Trophy className="h-4 w-4" aria-hidden />
              <span>{t("nav.leagues")}</span>
            </a>
          </li>
          <li>
            <a
              className="flex items-center gap-2 rounded px-3 py-2 min-h-12 hover:bg-gray-100"
              href="/dashboard"
            >
              <LayoutDashboard className="h-4 w-4" aria-hidden />
              <span>{t("nav.dashboard")}</span>
            </a>
          </li>
        </ul>
      </nav>
    </>
  );
}
