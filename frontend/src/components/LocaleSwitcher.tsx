"use client";

import React from "react";
import { useI18n } from "../app/i18n";

export default function LocaleSwitcher() {
  const { locale, setLocale, t } = useI18n();

  const getLocaleCode = (locale: string) => {
    return locale.split("-")[0].toUpperCase();
  };

  return (
    <select
      aria-label={t("actions.language")}
      className="rounded border border-[var(--border)] bg-[var(--color-surface)] px-2 py-1 text-sm text-[var(--color-text)] hover:bg-[var(--color-elevated)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
      value={locale}
      onChange={(e) => setLocale(e.target.value)}
      title={t("actions.language")}
    >
      <option value="en-US">EN</option>
      <option value="es-ES">ES</option>
    </select>
  );
}
