"use client";

import React from "react";
import { useI18n } from "../app/i18n";

export default function LocaleSwitcher() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="inline-flex items-center gap-2 text-sm">
      <span className="text-gray-700">{t('actions.language')}</span>
      <select
        aria-label={t('actions.language')}
        className="rounded border px-2 py-1"
        value={locale}
        onChange={(e) => setLocale(e.target.value)}
      >
        <option value="en-US">English</option>
        <option value="es-ES">Español</option>
      </select>
    </label>
  );
}

