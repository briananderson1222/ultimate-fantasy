"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { z } from "zod";
import { Card, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { useToast } from "../../components/ui/toast";
import { PageHeader } from "../../components/ui/page-header";
import { Modal } from "../../components/ui/modal";

type Trade = {
  trade_id: string;
  from_team_id: string;
  to_team_id: string;
  offer: string[]; // player IDs
  request: string[]; // player IDs
  created_at: string; // ISO
  status: "proposed" | "cancelled" | "accepted" | "rejected";
};

function loadTrades(): Trade[] {
  try {
    const raw = localStorage.getItem("uf_trades");
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed as Trade[];
    return [];
  } catch {
    return [];
  }
}

function saveTrades(items: Trade[]) {
  try {
    localStorage.setItem("uf_trades", JSON.stringify(items));
  } catch {}
}

function uid() {
  return (typeof crypto !== "undefined" && "randomUUID" in crypto ? (crypto as any).randomUUID() : "t_" + Math.random().toString(36).slice(2));
}

export default function TradesPage() {
  const toast = useToast();
  const [fromTeam, setFromTeam] = useState("");
  const [toTeam, setToTeam] = useState("");
  const [offer, setOffer] = useState<string[]>([""]);
  const [request, setRequest] = useState<string[]>([""]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [trades, setTrades] = useState<Trade[]>([]);
  const [reviewOpen, setReviewOpen] = useState(false);

  useEffect(() => {
    setTrades(loadTrades());
  }, []);

  useEffect(() => {
    saveTrades(trades);
  }, [trades]);

  const schema = z.object({
    from_team_id: z.string().min(1, "Your team is required"),
    to_team_id: z.string().min(1, "Target team is required"),
    offer: z.array(z.string().trim()).transform((arr) => arr.filter(Boolean)),
    request: z.array(z.string().trim()).transform((arr) => arr.filter(Boolean)),
  }).refine((val) => val.offer.length > 0 || val.request.length > 0, {
    message: "Add at least one offered or requested player",
    path: ["offer"],
  });

  function setOfferAt(idx: number, value: string) {
    setOffer((prev) => prev.map((v, i) => (i === idx ? value : v)));
  }
  function setRequestAt(idx: number, value: string) {
    setRequest((prev) => prev.map((v, i) => (i === idx ? value : v)));
  }

  function addOffer() { setOffer((prev) => [...prev, ""]); }
  function addRequest() { setRequest((prev) => [...prev, ""]); }
  function removeOffer(idx: number) { setOffer((prev) => prev.filter((_, i) => i !== idx)); }
  function removeRequest(idx: number) { setRequest((prev) => prev.filter((_, i) => i !== idx)); }

  const canReview = useMemo(() => fromTeam && toTeam && (offer.some(Boolean) || request.some(Boolean)), [fromTeam, toTeam, offer, request]);

  function review() {
    const parsed = schema.safeParse({ from_team_id: fromTeam, to_team_id: toTeam, offer, request });
    if (!parsed.success) {
      const es: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const path = issue.path.join(".");
        es[path] = issue.message;
      }
      setErrors(es);
      return;
    }
    setErrors({});
    setReviewOpen(true);
  }

  function submit() {
    const parsed = schema.safeParse({ from_team_id: fromTeam, to_team_id: toTeam, offer, request });
    if (!parsed.success) return;
    const t: Trade = {
      trade_id: uid(),
      from_team_id: parsed.data.from_team_id,
      to_team_id: parsed.data.to_team_id,
      offer: parsed.data.offer,
      request: parsed.data.request,
      created_at: new Date().toISOString(),
      status: "proposed",
    };
    setTrades((prev) => [t, ...prev]);
    setReviewOpen(false);
    toast.show({ title: "Trade proposed", description: `${t.offer.length} for ${t.request.length}` });
  }

  function cancelTrade(id: string) {
    setTrades((prev) => prev.map((t) => (t.trade_id === id && t.status === "proposed" ? { ...t, status: "cancelled" } : t)));
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader title="Trades" />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Trade Builder</CardTitle>
          </CardHeader>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Your Team ID" value={fromTeam} onChange={(e) => setFromTeam(e.target.value)} />
            <Input label="Target Team ID" value={toTeam} onChange={(e) => setToTeam(e.target.value)} />
          </div>
          {errors.from_team_id && <p className="text-xs text-red-600">{errors.from_team_id}</p>}
          {errors.to_team_id && <p className="text-xs text-red-600">{errors.to_team_id}</p>}

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <div className="mb-1 text-sm font-medium">Offer Players</div>
              <div className="space-y-2">
                {offer.map((val, idx) => (
                  <div key={`offer-${idx}`} className="flex gap-2">
                    <input
                      className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                      placeholder="player uuid"
                      value={val}
                      onChange={(e) => setOfferAt(idx, e.target.value)}
                    />
                    <button className="rounded bg-red-100 px-3 py-2 text-red-700" onClick={() => removeOffer(idx)}>Remove</button>
                  </div>
                ))}
                <button className="rounded bg-gray-200 px-3 py-1 text-sm" onClick={addOffer}>Add Player</button>
              </div>
              {errors.offer && <p className="mt-1 text-xs text-red-600">{errors.offer}</p>}
            </div>
            <div>
              <div className="mb-1 text-sm font-medium">Request Players</div>
              <div className="space-y-2">
                {request.map((val, idx) => (
                  <div key={`request-${idx}`} className="flex gap-2">
                    <input
                      className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                      placeholder="player uuid"
                      value={val}
                      onChange={(e) => setRequestAt(idx, e.target.value)}
                    />
                    <button className="rounded bg-red-100 px-3 py-2 text-red-700" onClick={() => removeRequest(idx)}>Remove</button>
                  </div>
                ))}
                <button className="rounded bg-gray-200 px-3 py-1 text-sm" onClick={addRequest}>Add Player</button>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button disabled={!canReview} onClick={review}>Review Trade</Button>
            <span className="text-xs text-gray-600">No API yet — demo only</span>
          </div>
        </Card>

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>My Trades</CardTitle>
          </CardHeader>
          {trades.length === 0 && (
            <div className="py-2 text-sm text-gray-600">No trades yet.</div>
          )}
          {trades.length > 0 && (
            <ul className="grid gap-3 sm:grid-cols-2">
              {trades.map((t) => (
                <li key={t.trade_id} className="surface rounded-[var(--radius-md)] p-3 border-l-4" style={{ borderLeftColor: t.status === 'proposed' ? '#2563eb' : t.status === 'accepted' ? '#16a34a' : t.status === 'rejected' ? '#dc2626' : '#6b7280' }}>
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium truncate">{String(t.from_team_id).slice(0,6)} ⇄ {String(t.to_team_id).slice(0,6)}</div>
                    <Badge variant={t.status === 'accepted' ? 'success' : t.status === 'rejected' || t.status === 'cancelled' ? 'secondary' : 'default'}>{t.status}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-[var(--color-muted)]">{new Date(t.created_at).toLocaleString()}</div>
                  <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-xs font-medium">Offer</div>
                      <ul className="mt-1 space-y-1">
                        {t.offer.length ? t.offer.map((p, i) => <li key={i} className="rounded bg-gray-50 px-2 py-1">{p.slice(0,8)}</li>) : <li className="text-xs text-gray-500">—</li>}
                      </ul>
                    </div>
                    <div>
                      <div className="text-xs font-medium">Request</div>
                      <ul className="mt-1 space-y-1">
                        {t.request.length ? t.request.map((p, i) => <li key={i} className="rounded bg-gray-50 px-2 py-1">{p.slice(0,8)}</li>) : <li className="text-xs text-gray-500">—</li>}
                      </ul>
                    </div>
                  </div>
                  {t.status === "proposed" && (
                    <div className="mt-3 flex items-center justify-end">
                      <Button variant="ghost" onClick={() => cancelTrade(t.trade_id)}>Cancel</Button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
          <div className="text-xs text-gray-600">Local-only demo; persists to browser storage.</div>
        </Card>

        <Modal open={reviewOpen} onClose={() => setReviewOpen(false)} title="Review Trade">
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-600">From:</span> {fromTeam}</div>
            <div><span className="text-gray-600">To:</span> {toTeam}</div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-medium">Offer</div>
                <ul className="mt-1 space-y-1">
                  {offer.filter(Boolean).map((p, i) => <li key={`off-${i}`} className="rounded bg-gray-50 px-2 py-1">{p}</li>)}
                  {offer.filter(Boolean).length === 0 && <li className="text-xs text-gray-500">—</li>}
                </ul>
              </div>
              <div>
                <div className="text-xs font-medium">Request</div>
                <ul className="mt-1 space-y-1">
                  {request.filter(Boolean).map((p, i) => <li key={`req-${i}`} className="rounded bg-gray-50 px-2 py-1">{p}</li>)}
                  {request.filter(Boolean).length === 0 && <li className="text-xs text-gray-500">—</li>}
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center justify-end gap-2">
            <Button variant="ghost" onClick={() => setReviewOpen(false)}>Back</Button>
            <Button onClick={submit}>Submit Trade</Button>
          </div>
        </Modal>
      </div>
    </main>
  );
}

