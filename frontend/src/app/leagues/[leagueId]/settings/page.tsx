"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { updateLeagueSettings } from "../../../../services/api";
import { PageHeader } from "../../../../components/ui/page-header";
import { Card, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Button } from "../../../../components/ui/button";
import { Input } from "../../../../components/ui/input";
import { useToast } from "../../../../components/ui/toast";

type KV = Record<string, number>;

const kvSchema = z.record(z.number());

const SCHEMAS: Record<string, { label: string; schema: z.ZodTypeAny; template: any } | undefined> =
  {
    "scoring.basketball": {
      label: "Basketball Scoring (points per stat)",
      schema: kvSchema,
      template: { PTS: 1, REB: 1.2, AST: 1.5, STL: 3, BLK: 3, TOV: -1 },
    },
    "lineup.positions": {
      label: "Lineup Positions (slots per position)",
      schema: kvSchema,
      template: { PG: 1, SG: 1, SF: 1, PF: 1, C: 1, UTIL: 2 },
    },
    "roster.limits": {
      label: "Roster Limits (max count per position)",
      schema: kvSchema,
      template: { G: 5, F: 5, C: 3 },
    },
  };

function tryParse(json: string): { ok: true; value: any } | { ok: false; error: string } {
  try {
    return { ok: true, value: JSON.parse(json) };
  } catch (e: any) {
    return { ok: false, error: String(e?.message || e) };
  }
}

export default function LeagueSettingsPage() {
  const params = useParams<{ leagueId: string }>();
  const leagueId = params?.leagueId || "";
  const toast = useToast();

  const [ruleName, setRuleName] = useState<string>("scoring.basketball");
  const [rows, setRows] = useState<Array<{ key: string; value: number }>>([]);
  const [advanced, setAdvanced] = useState(false);
  const [json, setJson] = useState<string>("{}");
  const [jsonError, setJsonError] = useState<string>("");
  const [activeJson, setActiveJson] = useState<string>("{}");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const preset = useMemo(() => SCHEMAS[ruleName], [ruleName]);

  // Load last-saved active value from localStorage per league+rule
  useEffect(() => {
    try {
      const key = `uf_rules:${leagueId}:${ruleName}`;
      const saved = localStorage.getItem(key);
      if (saved) setActiveJson(saved);
      else setActiveJson(JSON.stringify(preset?.template ?? {}, null, 2));
    } catch {}
  }, [leagueId, ruleName, preset]);

  useEffect(() => {
    // Load template when switching rule types
    if (preset) {
      const obj = preset.template as KV;
      setRows(Object.entries(obj).map(([k, v]) => ({ key: k, value: v })));
      setJson(JSON.stringify(obj, null, 2));
      setJsonError("");
      setAdvanced(false);
    } else {
      setRows([]);
      setJson("{}");
      setJsonError("");
      setAdvanced(true);
    }
  }, [preset]);

  // Keep JSON in sync with simple editor rows
  useEffect(() => {
    if (advanced) return; // advanced mode directly edits JSON
    const obj: KV = {};
    for (const r of rows) {
      if (!r.key) continue;
      obj[r.key] = Number(r.value);
    }
    setJson(JSON.stringify(obj, null, 2));
  }, [rows, advanced]);

  const updateSettings = useMutation({
    mutationFn: async (payload: { name: string; value: any }) =>
      updateLeagueSettings(leagueId, payload),
    onSuccess: (data) => {
      toast.show({ title: "Settings saved", description: data.name });
      try {
        const key = `uf_rules:${leagueId}:${ruleName}`;
        localStorage.setItem(key, JSON.stringify(data.value, null, 2));
        setActiveJson(JSON.stringify(data.value, null, 2));
      } catch {}
    },
    onError: (err: any) => {
      toast.show({ title: "Save failed", description: String(err?.message || err) });
    },
  });

  function addRow() {
    setRows((r) => [...r, { key: "", value: 0 }]);
  }
  function removeRow(i: number) {
    setRows((r) => r.filter((_, idx) => idx !== i));
  }

  function validate(): { ok: true; value: any } | { ok: false; error: string } {
    const parsed = tryParse(json);
    if (!parsed.ok) return parsed;
    if (preset) {
      const res = preset.schema.safeParse(parsed.value);
      if (!res.success)
        return { ok: false, error: res.error.errors.map((e) => e.message).join("; ") };
    }
    return { ok: true, value: parsed.value };
  }

  function submit() {
    const res = validate();
    if (!res.ok) {
      setJsonError(res.error);
      return;
    }
    setJsonError("");
    updateSettings.mutate({ name: ruleName || "custom", value: res.value });
  }

  function copyJson() {
    try {
      navigator.clipboard.writeText(json);
      toast.show({ title: "Copied JSON" });
    } catch {}
  }

  function downloadJson() {
    try {
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${ruleName || "rules"}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {}
  }

  function importFromFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "{}");
      setJson(text);
      setAdvanced(true);
      setJsonError("");
    };
    reader.readAsText(file);
    // reset input so same file can be selected again
    e.target.value = "";
  }

  function revertToActive() {
    setJson(activeJson);
    setJsonError("");
    setAdvanced(true);
  }

  function parseKV(s: string): KV {
    const parsed = tryParse(s);
    if (!parsed.ok) return {};
    const obj = parsed.value as Record<string, any>;
    const out: KV = {};
    for (const [k, v] of Object.entries(obj)) {
      out[k] = Number(v as any);
    }
    return out;
  }

  const diff = useMemo(() => {
    // shallow diff for KV-like objects
    const oldObj = parseKV(activeJson);
    const newObj = parseKV(json);
    const changed: Array<{ key: string; from: number | string; to: number | string }> = [];
    const added: Array<{ key: string; to: number | string }> = [];
    const removed: Array<{ key: string; from: number | string }> = [];
    const oldKeys = new Set(Object.keys(oldObj));
    const newKeys = new Set(Object.keys(newObj));
    for (const k of newKeys) {
      if (!oldKeys.has(k)) {
        added.push({ key: k, to: newObj[k] });
      } else if (oldObj[k] !== newObj[k]) {
        changed.push({ key: k, from: oldObj[k], to: newObj[k] });
      }
    }
    for (const k of oldKeys) {
      if (!newKeys.has(k)) removed.push({ key: k, from: oldObj[k] });
    }
    return { changed, added, removed };
  }, [activeJson, json]);

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader
          title="League Settings"
          actions={
            <Link className="text-blue-700 underline" href={`/leagues/${leagueId}`}>
              Back
            </Link>
          }
        />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Rule Editor</CardTitle>
          </CardHeader>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="text-sm text-gray-700">
              Rule Name
              <select
                className="mt-1 w-full rounded border px-3 py-2"
                value={ruleName}
                onChange={(e) => setRuleName(e.target.value)}
              >
                {Object.entries(SCHEMAS).map(([key, s]) => (
                  <option key={key} value={key}>
                    {s?.label ?? key}
                  </option>
                ))}
                <option value="custom">Custom (JSON)</option>
              </select>
            </label>

            <label className="text-sm text-gray-700 inline-flex items-center gap-2">
              <input
                type="checkbox"
                checked={advanced}
                onChange={(e) => setAdvanced(e.target.checked)}
              />
              Use advanced JSON editor
            </label>
          </div>

          {!advanced && preset && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">Edit values</div>
                <Button variant="secondary" onClick={addRow}>
                  Add Row
                </Button>
              </div>
              {rows.map((r, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <Input
                    label="Key"
                    value={r.key}
                    onChange={(e) =>
                      setRows((arr) =>
                        arr.map((it, i) => (i === idx ? { ...it, key: e.target.value } : it)),
                      )
                    }
                  />
                  <Input
                    label="Value"
                    inputMode="decimal"
                    value={String(r.value)}
                    onChange={(e) =>
                      setRows((arr) =>
                        arr.map((it, i) =>
                          i === idx ? { ...it, value: Number(e.target.value) } : it,
                        ),
                      )
                    }
                  />
                  <button
                    className="rounded bg-red-100 px-3 py-2 text-red-700 mt-6"
                    onClick={() => removeRow(idx)}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-sm text-gray-700">Value (JSON)</label>
            <textarea
              className="h-48 w-full rounded border p-2 font-mono text-sm"
              value={json}
              onChange={(e) => setJson(e.target.value)}
              aria-invalid={jsonError ? true : undefined}
              aria-describedby={jsonError ? "json-error" : undefined}
            />
            {jsonError && (
              <p id="json-error" className="text-sm text-red-600">
                {jsonError}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <Button variant="secondary" onClick={copyJson}>
                Copy JSON
              </Button>
              <Button variant="secondary" onClick={downloadJson}>
                Download JSON
              </Button>
              <input
                ref={fileInputRef}
                onChange={importFromFile}
                type="file"
                accept="application/json"
                className="hidden"
              />
              <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                Import JSON
              </Button>
              <Button variant="ghost" onClick={revertToActive}>
                Revert to Active
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={submit}
              loading={updateSettings.isPending}
              disabled={updateSettings.isPending}
            >
              Save
            </Button>
            {updateSettings.isError && (
              <span className="text-sm text-red-600">
                {(updateSettings.error as Error)?.message}
              </span>
            )}
          </div>
        </Card>

        <Card className="space-y-2">
          <CardHeader>
            <CardTitle>Preview Changes</CardTitle>
          </CardHeader>
          <div className="text-sm text-gray-700">
            Comparing edited JSON against active rules (not yet saved).
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <div className="font-medium">Changed</div>
              <ul className="mt-1 list-inside list-disc text-sm">
                {diff.changed.length === 0 && <li className="text-gray-500">None</li>}
                {diff.changed.map((c) => (
                  <li key={c.key}>
                    {c.key}: <span className="text-red-700">{String(c.from)}</span> →{" "}
                    <span className="text-green-700">{String(c.to)}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-medium">Added</div>
              <ul className="mt-1 list-inside list-disc text-sm">
                {diff.added.length === 0 && <li className="text-gray-500">None</li>}
                {diff.added.map((a) => (
                  <li key={a.key}>
                    {a.key}: <span className="text-green-700">{String(a.to)}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-medium">Removed</div>
              <ul className="mt-1 list-inside list-disc text-sm">
                {diff.removed.length === 0 && <li className="text-gray-500">None</li>}
                {diff.removed.map((r) => (
                  <li key={r.key}>
                    {r.key}: <span className="text-red-700">{String(r.from)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </main>
  );
}
