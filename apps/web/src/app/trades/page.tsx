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
import { Clock, TrendingUp, TrendingDown, AlertCircle, CheckCircle, Scale, Bell } from "lucide-react";

type Player = {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  current_value: number;
  injury_status?: string;
};

type Trade = {
  trade_id: string;
  from_team_id: string;
  to_team_id: string;
  offer: string[]; // player IDs
  request: string[]; // player IDs
  created_at: string; // ISO
  deadline?: string; // ISO
  status: "proposed" | "cancelled" | "accepted" | "rejected" | "expired";
  fairness_score?: number; // 0-100, higher = more fair
  notes?: string;
};

type TradeAnalysis = {
  offer_value: number;
  request_value: number;
  value_difference: number;
  fairness_score: number;
  recommendation: "accept" | "reject" | "negotiate";
  reasons: string[];
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
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? (crypto as any).randomUUID()
    : "t_" + Math.random().toString(36).slice(2);
}

// Mock player database for demo
const MOCK_PLAYERS: Record<string, Player> = {
  "p1": { id: "p1", name: "LeBron James", position: "SF", team: "LAL", projected_points: 52.5, current_value: 95 },
  "p2": { id: "p2", name: "Stephen Curry", position: "PG", team: "GSW", projected_points: 48.2, current_value: 92 },
  "p3": { id: "p3", name: "Kevin Durant", position: "PF", team: "PHX", projected_points: 46.8, current_value: 90 },
  "p4": { id: "p4", name: "Giannis Antetokounmpo", position: "PF", team: "MIL", projected_points: 55.1, current_value: 98 },
  "p5": { id: "p5", name: "Luka Dončić", position: "PG", team: "DAL", projected_points: 50.3, current_value: 94 },
  "p6": { id: "p6", name: "Jayson Tatum", position: "SF", team: "BOS", projected_points: 45.7, current_value: 88 },
  "p7": { id: "p7", name: "Nikola Jokić", position: "C", team: "DEN", projected_points: 52.8, current_value: 96 },
  "p8": { id: "p8", name: "Joel Embiid", position: "C", team: "PHI", projected_points: 49.4, current_value: 91, injury_status: "questionable" },
};

// Trade analysis functions
function getPlayerInfo(playerId: string): Player | null {
  return MOCK_PLAYERS[playerId] || null;
}

function calculateTradeValue(playerIds: string[]): number {
  return playerIds.reduce((total, id) => {
    const player = getPlayerInfo(id);
    return total + (player?.current_value || 0);
  }, 0);
}

function analyzeTradeProposal(offer: string[], request: string[]): TradeAnalysis {
  const offerValue = calculateTradeValue(offer);
  const requestValue = calculateTradeValue(request);
  const valueDifference = Math.abs(offerValue - requestValue);
  const averageValue = (offerValue + requestValue) / 2;
  const fairnessScore = Math.max(0, 100 - (valueDifference / averageValue * 100));

  const reasons: string[] = [];
  let recommendation: "accept" | "reject" | "negotiate" = "negotiate";

  // Analysis logic
  if (fairnessScore >= 85) {
    recommendation = "accept";
    reasons.push("Trade values are very close");
  } else if (fairnessScore >= 70) {
    recommendation = "negotiate";
    reasons.push("Trade is relatively fair but could be improved");
  } else {
    recommendation = "reject";
    reasons.push("Significant value imbalance");
  }

  // Check for injured players
  const injuredOffered = offer.some(id => getPlayerInfo(id)?.injury_status);
  const injuredRequested = request.some(id => getPlayerInfo(id)?.injury_status);

  if (injuredOffered && !injuredRequested) {
    reasons.push("You're offering injured player(s)");
  }
  if (injuredRequested && !injuredOffered) {
    reasons.push("Receiving injured player(s)");
  }

  // Position balance
  const offeredPositions = offer.map(id => getPlayerInfo(id)?.position).filter(Boolean);
  const requestedPositions = request.map(id => getPlayerInfo(id)?.position).filter(Boolean);

  if (new Set(offeredPositions).size !== new Set(requestedPositions).size) {
    reasons.push("Consider position balance in your lineup");
  }

  return {
    offer_value: offerValue,
    request_value: requestValue,
    value_difference: valueDifference,
    fairness_score: Math.round(fairnessScore),
    recommendation,
    reasons
  };
}

function getTradeDeadline(createdAt: string): string {
  const created = new Date(createdAt);
  const deadline = new Date(created.getTime() + 7 * 24 * 60 * 60 * 1000); // 7 days
  return deadline.toISOString();
}

function isTradeExpired(deadline: string): boolean {
  return new Date() > new Date(deadline);
}

function getTimeRemaining(deadline: string): string {
  const now = new Date();
  const end = new Date(deadline);
  const diff = end.getTime() - now.getTime();

  if (diff <= 0) return "Expired";

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days > 0) return `${days}d ${hours}h`;
  return `${hours}h`;
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
  const [tradeAnalysis, setTradeAnalysis] = useState<TradeAnalysis | null>(null);
  const [selectedTradeId, setSelectedTradeId] = useState<string | null>(null);
  const [showPlayerSearch, setShowPlayerSearch] = useState(false);
  const [playerSearchQuery, setPlayerSearchQuery] = useState("");
  const [selectedField, setSelectedField] = useState<{ type: 'offer' | 'request', index: number } | null>(null);

  useEffect(() => {
    setTrades(loadTrades());
  }, []);

  useEffect(() => {
    saveTrades(trades);
  }, [trades]);

  // Real-time trade analysis
  useEffect(() => {
    const validOffer = offer.filter(Boolean);
    const validRequest = request.filter(Boolean);

    if (validOffer.length > 0 || validRequest.length > 0) {
      const analysis = analyzeTradeProposal(validOffer, validRequest);
      setTradeAnalysis(analysis);
    } else {
      setTradeAnalysis(null);
    }
  }, [offer, request]);

  // Available players for search
  const availablePlayers = useMemo(() => {
    return Object.values(MOCK_PLAYERS).filter(player =>
      player.name.toLowerCase().includes(playerSearchQuery.toLowerCase()) ||
      player.position.toLowerCase().includes(playerSearchQuery.toLowerCase()) ||
      player.team.toLowerCase().includes(playerSearchQuery.toLowerCase())
    );
  }, [playerSearchQuery]);

  const schema = z
    .object({
      from_team_id: z.string().min(1, "Your team is required"),
      to_team_id: z.string().min(1, "Target team is required"),
      offer: z.array(z.string().trim()).transform((arr) => arr.filter(Boolean)),
      request: z.array(z.string().trim()).transform((arr) => arr.filter(Boolean)),
    })
    .refine((val) => val.offer.length > 0 || val.request.length > 0, {
      message: "Add at least one offered or requested player",
      path: ["offer"],
    });

  function setOfferAt(idx: number, value: string) {
    setOffer((prev) => prev.map((v, i) => (i === idx ? value : v)));
  }
  function setRequestAt(idx: number, value: string) {
    setRequest((prev) => prev.map((v, i) => (i === idx ? value : v)));
  }

  function addOffer() {
    setOffer((prev) => [...prev, ""]);
  }
  function addRequest() {
    setRequest((prev) => [...prev, ""]);
  }
  function removeOffer(idx: number) {
    setOffer((prev) => prev.filter((_, i) => i !== idx));
  }
  function removeRequest(idx: number) {
    setRequest((prev) => prev.filter((_, i) => i !== idx));
  }

  const canReview = useMemo(
    () => fromTeam && toTeam && (offer.some(Boolean) || request.some(Boolean)),
    [fromTeam, toTeam, offer, request],
  );

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

  function selectPlayer(playerId: string) {
    if (!selectedField) return;

    const { type, index } = selectedField;
    if (type === 'offer') {
      setOfferAt(index, playerId);
    } else {
      setRequestAt(index, playerId);
    }
    setShowPlayerSearch(false);
    setSelectedField(null);
    setPlayerSearchQuery("");
  }

  function submit() {
    const parsed = schema.safeParse({ from_team_id: fromTeam, to_team_id: toTeam, offer, request });
    if (!parsed.success) return;

    const createdAt = new Date().toISOString();
    const deadline = getTradeDeadline(createdAt);
    const analysis = tradeAnalysis;

    const t: Trade = {
      trade_id: uid(),
      from_team_id: parsed.data.from_team_id,
      to_team_id: parsed.data.to_team_id,
      offer: parsed.data.offer,
      request: parsed.data.request,
      created_at: createdAt,
      deadline,
      status: "proposed",
      fairness_score: analysis?.fairness_score,
      notes: analysis?.reasons.join("; "),
    };
    setTrades((prev) => [t, ...prev]);
    setReviewOpen(false);
    toast.show({
      title: "Trade proposed",
      description: `Fairness: ${analysis?.fairness_score || 0}/100`,
    });
  }

  function cancelTrade(id: string) {
    setTrades((prev) =>
      prev.map((t) =>
        t.trade_id === id && t.status === "proposed" ? { ...t, status: "cancelled" } : t,
      ),
    );
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader title="Trades" />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Trade Builder
              <div className="flex items-center gap-2">
                {tradeAnalysis && (
                  <Badge
                    variant={
                      tradeAnalysis.recommendation === "accept"
                        ? "success"
                        : tradeAnalysis.recommendation === "reject"
                          ? "secondary"
                          : "default"
                    }
                  >
                    <Scale className="h-3 w-3 mr-1" />
                    {tradeAnalysis.fairness_score}/100
                  </Badge>
                )}
              </div>
            </CardTitle>
          </CardHeader>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Your Team ID"
              value={fromTeam}
              onChange={(e) => setFromTeam(e.target.value)}
            />
            <Input
              label="Target Team ID"
              value={toTeam}
              onChange={(e) => setToTeam(e.target.value)}
            />
          </div>
          {errors.from_team_id && <p className="text-xs text-red-600">{errors.from_team_id}</p>}
          {errors.to_team_id && <p className="text-xs text-red-600">{errors.to_team_id}</p>}

          {/* Trade Analysis Card */}
          {tradeAnalysis && (
            <div className={`rounded-lg border p-3 ${
              tradeAnalysis.recommendation === "accept"
                ? "bg-green-50 border-green-200"
                : tradeAnalysis.recommendation === "reject"
                  ? "bg-red-50 border-red-200"
                  : "bg-yellow-50 border-yellow-200"
            }`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Scale className="h-4 w-4" />
                  <span className="font-medium text-sm">Trade Analysis</span>
                </div>
                <div className="flex items-center gap-2">
                  {tradeAnalysis.recommendation === "accept" && <CheckCircle className="h-4 w-4 text-green-600" />}
                  {tradeAnalysis.recommendation === "reject" && <AlertCircle className="h-4 w-4 text-red-600" />}
                  {tradeAnalysis.recommendation === "negotiate" && <TrendingUp className="h-4 w-4 text-yellow-600" />}
                  <span className="text-sm font-medium capitalize">{tradeAnalysis.recommendation}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <div className="font-medium">Offer Value: {tradeAnalysis.offer_value}</div>
                  <div className="font-medium">Request Value: {tradeAnalysis.request_value}</div>
                </div>
                <div>
                  <div className="font-medium">Difference: {tradeAnalysis.value_difference}</div>
                  <div className="font-medium">Fairness: {tradeAnalysis.fairness_score}/100</div>
                </div>
              </div>
              {tradeAnalysis.reasons.length > 0 && (
                <div className="mt-2">
                  <ul className="text-xs space-y-1">
                    {tradeAnalysis.reasons.map((reason, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span className="w-1 h-1 rounded-full bg-current mt-1.5 flex-shrink-0" />
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

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
                    <button
                      className="rounded bg-red-100 px-3 py-2 text-red-700"
                      onClick={() => removeOffer(idx)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button className="rounded bg-gray-200 px-3 py-1 text-sm" onClick={addOffer}>
                  Add Player
                </button>
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
                    <button
                      className="rounded bg-red-100 px-3 py-2 text-red-700"
                      onClick={() => removeRequest(idx)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button className="rounded bg-gray-200 px-3 py-1 text-sm" onClick={addRequest}>
                  Add Player
                </button>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button disabled={!canReview} onClick={review}>
              Review Trade
            </Button>
            <span className="text-xs text-gray-600">No API yet — demo only</span>
          </div>
        </Card>

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>My Trades</CardTitle>
          </CardHeader>
          {trades.length === 0 && <div className="py-2 text-sm text-gray-600">No trades yet.</div>}
          {trades.length > 0 && (
            <ul className="grid gap-3 sm:grid-cols-2">
              {trades.map((t) => (
                <li
                  key={t.trade_id}
                  className="surface rounded-[var(--radius-md)] p-3 border-l-4"
                  style={{
                    borderLeftColor:
                      t.status === "proposed"
                        ? "#2563eb"
                        : t.status === "accepted"
                          ? "#16a34a"
                          : t.status === "rejected"
                            ? "#dc2626"
                            : "#6b7280",
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium truncate">
                      {String(t.from_team_id).slice(0, 6)} ⇄ {String(t.to_team_id).slice(0, 6)}
                    </div>
                    <Badge
                      variant={
                        t.status === "accepted"
                          ? "success"
                          : t.status === "rejected" || t.status === "cancelled"
                            ? "secondary"
                            : "default"
                      }
                    >
                      {t.status}
                    </Badge>
                  </div>
                  <div className="mt-1 text-xs text-[var(--color-muted)]">
                    {new Date(t.created_at).toLocaleString()}
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-xs font-medium">Offer</div>
                      <ul className="mt-1 space-y-1">
                        {t.offer.length ? (
                          t.offer.map((p, i) => (
                            <li key={i} className="rounded bg-gray-50 px-2 py-1">
                              {p.slice(0, 8)}
                            </li>
                          ))
                        ) : (
                          <li className="text-xs text-gray-500">—</li>
                        )}
                      </ul>
                    </div>
                    <div>
                      <div className="text-xs font-medium">Request</div>
                      <ul className="mt-1 space-y-1">
                        {t.request.length ? (
                          t.request.map((p, i) => (
                            <li key={i} className="rounded bg-gray-50 px-2 py-1">
                              {p.slice(0, 8)}
                            </li>
                          ))
                        ) : (
                          <li className="text-xs text-gray-500">—</li>
                        )}
                      </ul>
                    </div>
                  </div>
                  {t.status === "proposed" && (
                    <div className="mt-3 flex items-center justify-end">
                      <Button variant="ghost" onClick={() => cancelTrade(t.trade_id)}>
                        Cancel
                      </Button>
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
            <div>
              <span className="text-gray-600">From:</span> {fromTeam}
            </div>
            <div>
              <span className="text-gray-600">To:</span> {toTeam}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-medium">Offer</div>
                <ul className="mt-1 space-y-1">
                  {offer.filter(Boolean).map((p, i) => (
                    <li key={`off-${i}`} className="rounded bg-gray-50 px-2 py-1">
                      {p}
                    </li>
                  ))}
                  {offer.filter(Boolean).length === 0 && (
                    <li className="text-xs text-gray-500">—</li>
                  )}
                </ul>
              </div>
              <div>
                <div className="text-xs font-medium">Request</div>
                <ul className="mt-1 space-y-1">
                  {request.filter(Boolean).map((p, i) => (
                    <li key={`req-${i}`} className="rounded bg-gray-50 px-2 py-1">
                      {p}
                    </li>
                  ))}
                  {request.filter(Boolean).length === 0 && (
                    <li className="text-xs text-gray-500">—</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center justify-end gap-2">
            <Button variant="ghost" onClick={() => setReviewOpen(false)}>
              Back
            </Button>
            <Button onClick={submit}>Submit Trade</Button>
          </div>
        </Modal>
      </div>
    </main>
  );
}
