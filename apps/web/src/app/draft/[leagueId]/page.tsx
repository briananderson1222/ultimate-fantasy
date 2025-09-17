"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Button } from "../../../components/ui/button";
import { Card, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Badge } from "../../../components/ui/badge";
import { Clock, Plus, ChevronUp, ChevronDown, Trash2, Send } from "lucide-react";

type Player = { id: string; name: string; pos: string; team: string; rank: number };
type Pick = { pickNo: number; player: Player; teamId?: string | null; ts: number };
type ChatMsg = { id: string; user: string; text: string; ts: number };

const POSITIONS = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"] as const;

function makeSamplePlayers(): Player[] {
  const names = [
    "John Adams",
    "Chris Baker",
    "Alex Carter",
    "Derrick Evans",
    "Felix Gomez",
    "Hank Irving",
    "Ivan Johnson",
    "Kyle Lewis",
    "Mason Neal",
    "Owen Park",
    "Quinn Reed",
    "Sean Thomas",
    "Uri Vega",
    "Will Young",
    "Zane Moore",
  ];
  const teams = ["NYJ", "DAL", "SF", "KC", "MIA", "BAL", "BUF", "GB", "LAR", "SEA"];
  const poss = ["QB", "RB", "WR", "TE"];
  const res: Player[] = [];
  let rank = 1;
  for (let i = 0; i < 60; i++) {
    const name =
      names[i % names.length] + (i >= names.length ? ` ${Math.floor(i / names.length)}` : "");
    res.push({
      id: cryptoRandomId(),
      name,
      pos: poss[i % poss.length],
      team: teams[i % teams.length],
      rank: rank++,
    });
  }
  return res;
}

function cryptoRandomId(): string {
  try {
    const arr = new Uint8Array(8);
    crypto.getRandomValues(arr);
    return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
  } catch {
    return Math.random().toString(36).slice(2);
  }
}

export default function DraftRoomPage() {
  const params = useParams<{ leagueId: string }>();
  const leagueId = params?.leagueId || "unknown";
  const storageKey = React.useMemo(() => `uf_draft_${leagueId}`, [leagueId]);
  const [_players, _setPlayers] = React.useState<Player[]>(() => makeSamplePlayers());
  const [filterPos, setFilterPos] = React.useState<(typeof POSITIONS)[number]>("ALL");
  const [query, setQuery] = React.useState("");
  const [queue, setQueue] = React.useState<Player[]>([]);
  const [picks, setPicks] = React.useState<Pick[]>([]);
  const [chat, setChat] = React.useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = React.useState("");
  const [seconds, setSeconds] = React.useState(60);
  const [running, setRunning] = React.useState(false);
  const searchRef = React.useRef<HTMLInputElement | null>(null);
  const chatRef = React.useRef<HTMLInputElement | null>(null);

  const teamId = React.useMemo(() => {
    try {
      return localStorage.getItem("uf_current_team_id") || undefined;
    } catch {
      return undefined;
    }
  }, []);

  // Load persisted state
  React.useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<{
        queue: Player[];
        picks: Pick[];
        chat: ChatMsg[];
        seconds: number;
        running: boolean;
      }>;
      if (parsed.queue) setQueue(parsed.queue);
      if (parsed.picks) setPicks(parsed.picks);
      if (parsed.chat) setChat(parsed.chat);
      if (typeof parsed.seconds === "number") setSeconds(parsed.seconds);
      if (typeof parsed.running === "boolean") setRunning(parsed.running);
    } catch {}
  }, [storageKey]);

  // Persist state
  React.useEffect(() => {
    try {
      const data = JSON.stringify({ queue, picks, chat, seconds, running });
      localStorage.setItem(storageKey, data);
    } catch {}
  }, [queue, picks, chat, seconds, running, storageKey]);

  // Timer
  React.useEffect(() => {
    if (!running) return;
    if (seconds <= 0) return;
    const id = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [running, seconds]);

  function resetTimer(next?: number) {
    setSeconds(typeof next === "number" ? next : 60);
    setRunning(false);
  }

  // Keyboard shortcuts
  React.useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "/") {
        e.preventDefault();
        searchRef.current?.focus();
      } else if (e.key.toLowerCase() === "q") {
        e.preventDefault();
        if (filtered[0]) addToQueue(filtered[0]);
      } else if (e.key === "Enter") {
        e.preventDefault();
        makePick();
      } else if (e.key.toLowerCase() === "c") {
        e.preventDefault();
        chatRef.current?.focus();
      } else if (e.key.toLowerCase() === "t") {
        e.preventDefault();
        setRunning((r) => !r);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Filters
  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    return _players
      .filter((p: any) => (filterPos === "ALL" ? true : p.pos === filterPos))
      .filter((p: any) =>
        q ? p.name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q) : true,
      )
      .slice(0, 100);
  }, [_players, filterPos, query]);

  function addToQueue(p: any) {
    if (queue.find((x) => x.id === p.id)) return;
    setQueue((q) => [...q, p]);
  }
  function removeFromQueue(id: string) {
    setQueue((q) => q.filter((x) => x.id !== id));
  }
  function moveInQueue(id: string, dir: -1 | 1) {
    setQueue((q) => {
      const idx = q.findIndex((x) => x.id === id);
      if (idx < 0) return q;
      const next = [...q];
      const to = Math.min(next.length - 1, Math.max(0, idx + dir));
      const [item] = next.splice(idx, 1);
      next.splice(to, 0, item);
      return next;
    });
  }
  function makePick() {
    setQueue((q) => {
      if (q.length === 0) return q;
      const [player, ...rest] = q;
      setPicks((ps) => [...ps, { pickNo: ps.length + 1, player, teamId, ts: Date.now() }]);
      // Reset timer on pick
      resetTimer(seconds || 60);
      return rest;
    });
  }
  function undoPick() {
    setPicks((ps) => ps.slice(0, -1));
  }

  function sendChat() {
    const text = chatInput.trim();
    if (!text) return;
    const user = (() => {
      try {
        return localStorage.getItem("uf_user_name") || "You";
      } catch {
        return "You";
      }
    })();
    setChat((c) => [...c, { id: cryptoRandomId(), user, text, ts: Date.now() }]);
    setChatInput("");
  }

  return (
    <main className="min-h-screen">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-4 p-3 md:grid-cols-12 md:p-4">
        {/* Picks Board */}
        <section className="md:col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>Live Picks</CardTitle>
            </CardHeader>
            <div className="flex items-center gap-2 px-4 pb-2">
              <Button variant="ghost" onClick={undoPick} disabled={picks.length === 0}>
                Undo last
              </Button>
              <div className="ml-auto text-xs text-[var(--color-muted)]" aria-live="polite">
                {picks.length} picks
              </div>
            </div>
            <ol className="max-h-[60vh] overflow-auto px-4 pb-4">
              {picks.map((pk) => (
                <li
                  key={pk.pickNo}
                  className="flex items-center justify-between border-b py-2"
                  style={{ borderColor: "var(--border)" }}
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{pk.pickNo}</Badge>
                    <div className="text-sm font-medium">{pk.player.name}</div>
                    <div className="text-xs text-[var(--color-muted)]">
                      {pk.player.pos} • {pk.player.team}
                    </div>
                  </div>
                  <div className="text-xs text-[var(--color-muted)]">
                    {pk.teamId ? String(pk.teamId).slice(0, 6) : "—"}
                  </div>
                </li>
              ))}
              {picks.length === 0 && (
                <li className="py-6 text-center text-sm text-[var(--color-muted)]">No picks yet</li>
              )}
            </ol>
          </Card>
        </section>

        {/* Player Search/List */}
        <section className="md:col-span-5">
          <Card>
            <CardHeader>
              <CardTitle>Players</CardTitle>
            </CardHeader>
            <div className="flex items-center gap-2 px-4 pb-3">
              <div className="flex-1">
                <Input
                  ref={searchRef as any}
                  placeholder="Search players or teams (press / to focus)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  aria-label="Search players"
                />
              </div>
              <label className="text-sm text-[var(--color-muted)]" htmlFor="pos">
                Pos
              </label>
              <select
                id="pos"
                className="rounded-[var(--radius-sm)] border px-[var(--space-2)] py-[calc(var(--space-1))] text-sm"
                style={{
                  background: "var(--color-surface)",
                  color: "var(--color-text)",
                  borderColor: "var(--border)",
                }}
                value={filterPos}
                onChange={(e) => setFilterPos(e.target.value as any)}
              >
                {POSITIONS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
            <ul className="max-h-[60vh] overflow-auto px-4 pb-4 text-sm">
              {filtered.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between border-b py-2"
                  style={{ borderColor: "var(--border)" }}
                >
                  <div className="min-w-0">
                    <div className="truncate font-medium">{p.name}</div>
                    <div className="text-xs text-[var(--color-muted)]">
                      {p.pos} • {p.team} • #{p.rank}
                    </div>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => addToQueue(p)}
                    leftIcon={<Plus className="h-4 w-4" aria-hidden />}
                  >
                    Queue
                  </Button>
                </li>
              ))}
              {filtered.length === 0 && (
                <li className="py-6 text-center text-sm text-[var(--color-muted)]">No results</li>
              )}
            </ul>
          </Card>
        </section>

        {/* Queue + Timer + Chat */}
        <section className="md:col-span-3 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-4 w-4" aria-hidden /> On the Clock
              </CardTitle>
            </CardHeader>
            <div className="flex items-center gap-2 px-4 pb-4">
              <div
                className="text-2xl tabular-nums"
                aria-live="polite"
                aria-label="Seconds remaining"
              >
                {String(Math.floor(seconds / 60)).padStart(2, "0")}:
                {String(seconds % 60).padStart(2, "0")}
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Button size="sm" variant="primary" onClick={() => setRunning((r) => !r)}>
                  {running ? "Pause" : "Start"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => resetTimer()}>
                  Reset
                </Button>
                <Button size="sm" variant="secondary" onClick={makePick}>
                  Pick
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>My Queue</CardTitle>
            </CardHeader>
            <ul className="max-h-[30vh] overflow-auto px-4 pb-4 text-sm">
              {queue.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between gap-2 border-b py-2"
                  style={{ borderColor: "var(--border)" }}
                >
                  <div className="min-w-0">
                    <div className="truncate font-medium">{p.name}</div>
                    <div className="text-xs text-[var(--color-muted)]">
                      {p.pos} • {p.team}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      aria-label="Move up"
                      className="rounded-[var(--radius-sm)] border p-1 hover:opacity-80"
                      style={{ borderColor: "var(--border)" }}
                      onClick={() => moveInQueue(p.id, -1)}
                    >
                      <ChevronUp className="h-4 w-4" aria-hidden />
                    </button>
                    <button
                      aria-label="Move down"
                      className="rounded-[var(--radius-sm)] border p-1 hover:opacity-80"
                      style={{ borderColor: "var(--border)" }}
                      onClick={() => moveInQueue(p.id, 1)}
                    >
                      <ChevronDown className="h-4 w-4" aria-hidden />
                    </button>
                    <button
                      aria-label="Remove"
                      className="rounded-[var(--radius-sm)] border p-1 hover:opacity-80"
                      style={{ borderColor: "var(--border)" }}
                      onClick={() => removeFromQueue(p.id)}
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>
                </li>
              ))}
              {queue.length === 0 && (
                <li className="py-6 text-center text-sm text-[var(--color-muted)]">
                  Queue is empty
                </li>
              )}
            </ul>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Chat</CardTitle>
            </CardHeader>
            <div className="flex h-[30vh] flex-col px-4 pb-3">
              <div
                className="mb-2 flex-1 overflow-auto rounded-[var(--radius-sm)] border p-2 text-sm"
                style={{ borderColor: "var(--border)" }}
              >
                {chat.length === 0 && (
                  <div className="text-center text-[var(--color-muted)]">No messages yet</div>
                )}
                {chat.map((m) => (
                  <div key={m.id} className="mb-1">
                    <span className="font-medium">{m.user}</span>{" "}
                    <span className="text-xs text-[var(--color-muted)]">
                      {new Date(m.ts).toLocaleTimeString()}
                    </span>
                    <div>{m.text}</div>
                  </div>
                ))}
              </div>
              <form
                className="flex items-center gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  sendChat();
                }}
              >
                <Input
                  ref={chatRef as any}
                  placeholder="Message (press Enter to send, C to focus)"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  aria-label="Chat message"
                />
                <Button
                  type="submit"
                  size="sm"
                  variant="secondary"
                  leftIcon={<Send className="h-4 w-4" aria-hidden />}
                >
                  Send
                </Button>
              </form>
            </div>
          </Card>
        </section>
      </div>
    </main>
  );
}
