"use client";

import React, { useMemo, useState } from "react";

type SortDir = "asc" | "desc";
type Column<T> = {
  key: string;
  header: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  hidden?: boolean;
};
type FilterOp = 'contains' | 'equals' | 'gt' | 'lt';
type Filter = { key: string; op: FilterOp; value: string };

type SavedViewState = {
  visible: Record<string, boolean>;
  sortKey: string;
  sortDir: SortDir;
  filters?: Filter[];
};

type DataTableProps<T> = {
  columns: Column<T>[];
  data: T[];
  initialSort?: { key: string; dir: SortDir };
  pageSize?: number;
  storageKey?: string; // when provided, enable saved views via localStorage
  shareKey?: string; // when provided, enable URL sharing via this query param
};

function compareValues(a: unknown, b: unknown) {
  const na = Number(a as any);
  const nb = Number(b as any);
  const aNum = !Number.isNaN(na) && `${a}`.trim() !== "" && isFinite(na);
  const bNum = !Number.isNaN(nb) && `${b}`.trim() !== "" && isFinite(nb);
  if (aNum && bNum) return na - nb;
  return String(a ?? "").localeCompare(String(b ?? ""), undefined, { numeric: true });
}

function loadViews(key: string | undefined): Record<string, SavedViewState> {
  if (!key) return {};
  try {
    const raw = localStorage.getItem(`dt:${key}:views`);
    return raw ? (JSON.parse(raw) as Record<string, SavedViewState>) : {};
  } catch {
    return {};
  }
}

function saveViews(key: string | undefined, views: Record<string, SavedViewState>) {
  if (!key) return;
  try {
    localStorage.setItem(`dt:${key}:views`, JSON.stringify(views));
  } catch {}
}

function loadLast(key: string | undefined): string | null {
  if (!key) return null;
  try {
    return localStorage.getItem(`dt:${key}:last`);
  } catch {
    return null;
  }
}

function saveLast(key: string | undefined, name: string | null) {
  if (!key) return;
  try {
    if (name) localStorage.setItem(`dt:${key}:last`, name);
    else localStorage.removeItem(`dt:${key}:last`);
  } catch {}
}

function encodeView(v: SavedViewState): string {
  try {
    const json = JSON.stringify(v);
    // URL-safe base64
    const b64 = typeof btoa === 'function' ? btoa(json) : Buffer.from(json, 'utf-8').toString('base64');
    return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  } catch {
    return '';
  }
}

function decodeView(s: string | null): SavedViewState | null {
  if (!s) return null;
  try {
    const b64 = s.replace(/-/g, '+').replace(/_/g, '/');
    const pad = b64.length % 4 === 0 ? '' : '='.repeat(4 - (b64.length % 4));
    const json = typeof atob === 'function' ? atob(b64 + pad) : Buffer.from(b64 + pad, 'base64').toString('utf-8');
    return JSON.parse(json) as SavedViewState;
  } catch {
    return null;
  }
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  initialSort,
  pageSize = 10,
  storageKey,
  shareKey,
}: DataTableProps<T>) {
  const [visible, setVisible] = useState<Record<string, boolean>>(() => {
    const v: Record<string, boolean> = {};
    for (const c of columns) v[c.key] = c.hidden ? false : true;
    return v;
  });
  const [sortKey, setSortKey] = useState<string>(initialSort?.key ?? "");
  const [sortDir, setSortDir] = useState<SortDir>(initialSort?.dir ?? "asc");
  const [page, setPage] = useState(0);
  const [views, setViews] = useState<Record<string, SavedViewState>>(() => loadViews(storageKey));
  const [selectedView, setSelectedView] = useState<string | "">(() => loadLast(storageKey) || "");
  const [filters, setFilters] = useState<Filter[]>([]);
  const [newFilter, setNewFilter] = useState<Filter>({ key: columns[0]?.key || '', op: 'contains', value: '' });

  // Apply last selected view on mount if present
  React.useEffect(() => {
    if (!storageKey) return;
    const last = loadLast(storageKey);
    if (last && views[last]) {
      const st = views[last];
      setVisible(st.visible);
      setSortKey(st.sortKey);
      setSortDir(st.sortDir);
      if (st.filters) setFilters(st.filters);
    }
  }, []);

  // Apply view from URL if present
  React.useEffect(() => {
    if (!shareKey) return;
    try {
      const usp = new URLSearchParams(window.location.search);
      const payload = usp.get(shareKey);
      const st = decodeView(payload);
      if (st) {
        setVisible(st.visible);
        setSortKey(st.sortKey);
        setSortDir(st.sortDir);
        setFilters(st.filters || []);
        setPage(0);
      }
    } catch {}
  }, [shareKey]);

  const visCols = useMemo(() => columns.filter((c) => visible[c.key]), [columns, visible]);

  const filtered = useMemo(() => {
    if (!filters.length) return data.slice();
    const rows = data.filter((row) => {
      return filters.every((f) => {
        const v = (row as any)[f.key];
        const raw = v == null ? '' : String(v);
        const val = f.value;
        const aNum = Number(raw);
        const bNum = Number(val);
        const bothNumeric = !Number.isNaN(aNum) && !Number.isNaN(bNum) && isFinite(aNum) && isFinite(bNum);
        switch (f.op) {
          case 'equals':
            return bothNumeric ? aNum === bNum : raw.toLowerCase() === val.toLowerCase();
          case 'gt':
            return bothNumeric ? aNum > bNum : raw > val;
          case 'lt':
            return bothNumeric ? aNum < bNum : raw < val;
          case 'contains':
          default:
            return raw.toLowerCase().includes(val.toLowerCase());
        }
      });
    });
    return rows;
  }, [data, filters]);

  const sorted = useMemo(() => {
    const rows = filtered.slice();
    if (!sortKey) return rows;
    rows.sort((ra, rb) => {
      const va = (ra as any)[sortKey];
      const vb = (rb as any)[sortKey];
      const cmp = compareValues(va, vb);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return rows;
  }, [filtered, sortKey, sortDir]);

  const total = sorted.length;
  const start = page * pageSize;
  const end = Math.min(start + pageSize, total);
  const pageRows = sorted.slice(start, end);

  function toggleSort(key: string) {
    if (sortKey !== key) {
      setSortKey(key);
      setSortDir("asc");
    } else {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    }
  }

  function saveCurrentView() {
    if (!storageKey) return;
    const name = window.prompt("Save view as:", selectedView || "My view");
    if (!name) return;
    const next = { ...views, [name]: { visible, sortKey, sortDir, filters } };
    setViews(next);
    saveViews(storageKey, next);
    setSelectedView(name);
    saveLast(storageKey, name);
  }

  function applyView(name: string) {
    setSelectedView(name);
    saveLast(storageKey, name);
    const st = views[name];
    if (!st) return;
    setVisible(st.visible);
    setSortKey(st.sortKey);
    setSortDir(st.sortDir);
    setFilters(st.filters || []);
    setPage(0);
  }

  function deleteView(name: string) {
    if (!storageKey) return;
    const next = { ...views };
    delete next[name];
    setViews(next);
    saveViews(storageKey, next);
    if (selectedView === name) {
      setSelectedView("");
      saveLast(storageKey, null);
    }
  }

  const [copied, setCopied] = useState(false);
  async function shareCurrentView() {
    if (!shareKey) return;
    const state: SavedViewState = { visible, sortKey, sortDir, filters };
    const enc = encodeView(state);
    const url = new URL(window.location.href);
    url.searchParams.set(shareKey, enc);
    try {
      await navigator.clipboard.writeText(url.toString());
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // fallback: update URL only
      window.history.replaceState({}, '', url.toString());
    }
  }

  return (
    <div className="w-full">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className="text-gray-700">Columns:</span>
          {columns.map((c) => (
            <label key={c.key} className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={!!visible[c.key]}
                onChange={() => setVisible((v) => ({ ...v, [c.key]: !v[c.key] }))}
              />
              <span>{c.header}</span>
            </label>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {/* Filters */}
          <details>
            <summary className="cursor-pointer rounded px-2 py-1 text-sm hover:bg-gray-100">Filters</summary>
            <div className="mt-2 flex flex-wrap items-end gap-2">
              <label className="text-sm text-gray-700">
                Column
                <select
                  className="ml-2 rounded border px-2 py-1"
                  value={newFilter.key}
                  onChange={(e) => setNewFilter((f) => ({ ...f, key: e.target.value }))}
                >
                  {columns.map((c) => (
                    <option key={c.key} value={c.key}>{c.header}</option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-gray-700">
                Op
                <select
                  className="ml-2 rounded border px-2 py-1"
                  value={newFilter.op}
                  onChange={(e) => setNewFilter((f) => ({ ...f, op: e.target.value as FilterOp }))}
                >
                  <option value="contains">contains</option>
                  <option value="equals">equals</option>
                  <option value="gt">&gt;</option>
                  <option value="lt">&lt;</option>
                </select>
              </label>
              <label className="text-sm text-gray-700">
                Value
                <input
                  className="ml-2 rounded border px-2 py-1"
                  value={newFilter.value}
                  onChange={(e) => setNewFilter((f) => ({ ...f, value: e.target.value }))}
                />
              </label>
              <button
                className="rounded bg-gray-200 px-2 py-1 text-sm disabled:opacity-50"
                onClick={() => {
                  if (!newFilter.key) return;
                  setFilters((fs) => [...fs, newFilter]);
                  setNewFilter({ key: newFilter.key, op: newFilter.op, value: '' });
                  setPage(0);
                }}
                disabled={!newFilter.key || newFilter.value.trim() === ''}
                type="button"
              >
                Add
              </button>
              {filters.length > 0 && (
                <button
                  className="rounded bg-gray-100 px-2 py-1 text-sm"
                  onClick={() => setFilters([])}
                  type="button"
                >
                  Clear
                </button>
              )}
            </div>
          </details>
          {storageKey && (
            <div className="flex items-center gap-2 text-sm">
              <label htmlFor={`dt-${storageKey}-views`} className="text-gray-700">
                Saved views
              </label>
              <select
                id={`dt-${storageKey}-views`}
                className="rounded border px-2 py-1"
                value={selectedView}
                onChange={(e) => applyView(e.target.value)}
              >
                <option value="">(none)</option>
                {Object.keys(views).map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
              <button
                className="rounded bg-gray-200 px-2 py-1"
                onClick={saveCurrentView}
                type="button"
              >
                Save View
              </button>
              <button
                className="rounded bg-gray-100 px-2 py-1 disabled:opacity-50"
                onClick={() => deleteView(selectedView)}
                disabled={!selectedView}
                type="button"
              >
                Delete
              </button>
              {shareKey && (
                <>
                  <button
                    className="rounded bg-indigo-600 px-2 py-1 text-white"
                    onClick={shareCurrentView}
                    type="button"
                  >
                    Share Link
                  </button>
                  <span className="text-xs text-green-700" aria-live="polite">
                    {copied ? 'Copied' : ''}
                  </span>
                </>
              )}
            </div>
          )}
          <div className="text-xs text-gray-600" aria-live="polite">
            {total ? `${start + 1}–${end} of ${total}` : "0 results"}
          </div>
        </div>
      </div>

      {filters.length > 0 && (
        <div className="mb-2 flex flex-wrap items-center gap-2" aria-label="Active filters">
          {filters.map((f, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-2 rounded-full px-2 py-0.5 text-xs"
              style={{ background: 'var(--color-elevated)', color: 'var(--color-text)', border: '1px solid var(--border)' }}
            >
              <span>
                {columns.find((c) => c.key === f.key)?.header || f.key} {f.op} "{f.value}"
              </span>
              <button
                aria-label={`Remove filter ${f.key} ${f.op} ${f.value}`}
                className="rounded bg-gray-200 px-1"
                onClick={() => setFilters((fs) => fs.filter((_, i) => i !== idx))}
                type="button"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse text-sm" style={{ color: 'var(--color-text)' }}>
          <thead>
            <tr className="border-b bg-gray-50">
              {/* header row */}
              {visCols.map((c) => {
                const sortedCol = sortKey === c.key;
                const ariaSort = sortedCol ? (sortDir === "asc" ? "ascending" : "descending") : "none";
                return (
                  <th
                    key={c.key}
                    scope="col"
                    className="whitespace-nowrap px-[var(--space-3)] py-[var(--space-2)] text-left font-medium"
                    style={{ background: 'var(--color-elevated)', color: 'var(--color-text)', borderBottom: '1px solid var(--border)' }}
                    aria-sort={ariaSort as any}
                  >
                    {c.sortable ? (
                      <button
                        className="inline-flex items-center gap-1 underline-offset-2 hover:underline"
                        onClick={() => toggleSort(c.key)}
                      >
                        {c.header}
                        {sortedCol && <span aria-hidden>{sortDir === "asc" ? "↑" : "↓"}</span>}
                      </button>
                    ) : (
                      c.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b hover:bg-[rgba(0,0,0,0.03)]" style={{ borderColor: 'var(--border)' }}>
                {visCols.map((c) => (
                  <td key={c.key} className="whitespace-nowrap px-[var(--space-3)] py-[var(--space-2)]">
                    {c.render ? c.render(row) : String((row as any)[c.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
            {pageRows.length === 0 && (
              <tr>
                <td className="px-[var(--space-3)] py-[var(--space-3)]" style={{ color: 'var(--color-muted)' }} colSpan={visCols.length}>
                  No data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-2 flex items-center justify-between">
        <button
          className="rounded-[var(--radius-sm)] px-[var(--space-3)] py-[var(--space-1)] text-sm disabled:opacity-50"
          style={{ background: 'var(--color-elevated)', color: 'var(--color-text)', border: '1px solid var(--border)' }}
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
        >
          Prev
        </button>
        <div className="text-xs text-gray-600">Page {total ? page + 1 : 0}</div>
        <button
          className="rounded-[var(--radius-sm)] px-[var(--space-3)] py-[var(--space-1)] text-sm disabled:opacity-50"
          style={{ background: 'var(--color-elevated)', color: 'var(--color-text)', border: '1px solid var(--border)' }}
          onClick={() => {
            const lastPage = Math.max(0, Math.ceil(total / pageSize) - 1);
            setPage((p) => Math.min(lastPage, p + 1));
          }}
          disabled={end >= total}
        >
          Next
        </button>
      </div>
    </div>
  );
}
