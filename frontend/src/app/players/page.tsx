"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { DataTable } from "../../components/ui/data-table";
import { PageHeader } from "../../components/ui/page-header";
import { Star } from "lucide-react";

type Player = {
  id: string;
  name: string;
  pos: "PG" | "SG" | "SF" | "PF" | "C";
  team: string;
  ppg: number;
  apg: number;
  rpg: number;
  rank: number;
};

const POSITIONS: Player["pos"][] = ["PG", "SG", "SF", "PF", "C"];
const TEAMS = ["NYJ", "DAL", "SF", "KC", "MIA", "BAL", "BUF", "GB", "LAR", "SEA"];
const FIRST = [
  "Alex",
  "Blake",
  "Casey",
  "Drew",
  "Evan",
  "Flynn",
  "Gray",
  "Hayden",
  "Indy",
  "Jules",
  "Kai",
  "Logan",
  "Morgan",
  "Nico",
  "Oak",
  "Parker",
  "Quinn",
  "Reese",
  "Sage",
  "Tatum",
  "Ari",
  "Brett",
  "Chase",
  "Devin",
  "Ellis",
  "Frankie",
  "Gale",
  "Harley",
  "Jamie",
  "Kris",
  "Lane",
  "Milan",
  "Noel",
  "Ocean",
  "Perry",
  "Riley",
  "Shay",
  "Taylor",
  "Val",
  "Winter",
];
const LAST = [
  "Anderson",
  "Bennett",
  "Carter",
  "Diaz",
  "Edwards",
  "Foster",
  "Garcia",
  "Hayes",
  "Iverson",
  "Jones",
  "Kim",
  "Lopez",
  "Miller",
  "Nguyen",
  "Owens",
  "Patel",
  "Quincy",
  "Reed",
  "Singh",
  "Turner",
  "Upton",
  "Vega",
  "White",
  "Xu",
  "Young",
  "Zimmer",
];

function hashNum(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0;
  return h >>> 0;
}

function genPlayers(count = 120): Player[] {
  const out: Player[] = [];
  let idx = 0;
  while (out.length < count) {
    const f = FIRST[idx % FIRST.length];
    const l = LAST[idx % LAST.length];
    const name = `${f} ${l}`;
    const team = TEAMS[idx % TEAMS.length];
    const pos = POSITIONS[idx % POSITIONS.length];
    const seed = hashNum(name + team + pos);
    const id = `p-${seed.toString(16)}`;
    const base = 10 + (seed % 26); // 10..35
    const ppg = Math.round((base + ((seed >> 3) % 10) / 10) * 10) / 10;
    const apg = Math.round((2 + (seed % 9) + ((seed >> 5) % 10) / 10) * 10) / 10;
    const rpg = Math.round((2 + (seed % 11) + ((seed >> 7) % 10) / 10) * 10) / 10;
    const rank = 1 + (seed % 300);
    out.push({ id, name, team, pos, ppg, apg, rpg, rank });
    idx++;
  }
  return out;
}

function loadFavorites(): Set<string> {
  try {
    const raw = localStorage.getItem("uf_favorites_players");
    const arr = raw ? (JSON.parse(raw) as string[]) : [];
    return new Set(arr);
  } catch {
    return new Set();
  }
}
function saveFavorites(set: Set<string>) {
  try {
    localStorage.setItem("uf_favorites_players", JSON.stringify(Array.from(set)));
  } catch {}
}

export default function PlayersPage() {
  const [search, setSearch] = useState("");
  const [pos, setPos] = useState<Set<Player["pos"]>>(new Set());
  const [team, setTeam] = useState<string>("");
  const [onlyFav, setOnlyFav] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  useEffect(() => setFavorites(loadFavorites()), []);
  useEffect(() => saveFavorites(favorites), [favorites]);

  const players = useMemo(() => genPlayers(150), []);

  const filtered = useMemo(() => {
    return players.filter((p) => {
      if (onlyFav && !favorites.has(p.id)) return false;
      if (pos.size && !pos.has(p.pos)) return false;
      if (team && p.team !== team) return false;
      if (search.trim()) {
        const q = search.trim().toLowerCase();
        const hay = `${p.name} ${p.team}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [players, search, pos, team, onlyFav, favorites]);

  function togglePos(v: Player["pos"]) {
    setPos((s) => {
      const next = new Set(s);
      next.has(v) ? next.delete(v) : next.add(v);
      return next;
    });
  }
  function toggleFav(id: string) {
    setFavorites((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <PageHeader title="Players" />

        <div
          className="sticky top-0 z-20 border-b bg-[var(--color-surface)]/95 backdrop-blur"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex flex-col gap-2 py-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <Input
                label="Search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name or team"
              />
              <div>
                <div className="mb-1 text-sm text-[var(--color-muted)]">Positions</div>
                <div className="flex flex-wrap gap-2">
                  {POSITIONS.map((p) => (
                    <button
                      key={p}
                      onClick={() => togglePos(p)}
                      className={`rounded-full px-3 py-1 text-sm border ${pos.has(p) ? "bg-blue-600 text-white border-blue-600" : "bg-transparent"}`}
                      style={!pos.has(p) ? { borderColor: "var(--border)" } : undefined}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm text-[var(--color-muted)]">Team</label>
                <select
                  className="w-full rounded-[var(--radius-md)] border px-[var(--space-3)] py-[var(--space-2)]"
                  style={{ borderColor: "var(--border)" }}
                  value={team}
                  onChange={(e) => setTeam(e.target.value)}
                >
                  <option value="">All</option>
                  {TEAMS.map((t) => (
                    <option value={t} key={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                className={`inline-flex items-center gap-2 rounded px-3 py-2 text-sm border ${onlyFav ? "bg-yellow-100 border-yellow-300" : ""}`}
                style={!onlyFav ? { borderColor: "var(--border)" } : undefined}
                onClick={() => setOnlyFav((v) => !v)}
              >
                <Star
                  className={`h-4 w-4 ${onlyFav ? "text-yellow-500" : "text-gray-500"}`}
                  aria-hidden
                />
                Favorites
              </button>
              {(pos.size > 0 || team || search || onlyFav) && (
                <button
                  className="rounded px-3 py-2 text-sm border"
                  style={{ borderColor: "var(--border)" }}
                  onClick={() => {
                    setSearch("");
                    setPos(new Set());
                    setTeam("");
                    setOnlyFav(false);
                  }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Mobile cards */}
        <div className="block sm:hidden">
          <div className="grid grid-cols-1 gap-3">
            {filtered.map((p) => (
              <div key={p.id} className="surface rounded-[var(--radius-md)] p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm font-medium">{p.name}</div>
                    <div className="text-xs text-[var(--color-muted)]">
                      {p.team} • {p.pos}
                    </div>
                  </div>
                  <button
                    aria-label={favorites.has(p.id) ? "Unfavorite" : "Favorite"}
                    onClick={() => toggleFav(p.id)}
                  >
                    <Star
                      className={`h-5 w-5 ${favorites.has(p.id) ? "text-yellow-500" : "text-gray-400"}`}
                      aria-hidden
                    />
                  </button>
                </div>
                <div className="mt-2 flex items-center gap-3 text-sm">
                  <div>
                    <span className="text-[var(--color-muted)]">PPG</span>{" "}
                    <span className="font-medium">{p.ppg.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-[var(--color-muted)]">APG</span>{" "}
                    <span className="font-medium">{p.apg.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-[var(--color-muted)]">RPG</span>{" "}
                    <span className="font-medium">{p.rpg.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <Card className="p-3 text-sm text-gray-600">No players match your filters.</Card>
            )}
          </div>
        </div>

        {/* Desktop table */}
        <div className="hidden sm:block">
          <Card>
            <CardHeader>
              <CardTitle>Players</CardTitle>
            </CardHeader>
            <div className="p-3">
              <DataTable<Player>
                data={filtered}
                pageSize={15}
                initialSort={{ key: "rank", dir: "asc" }}
                storageKey="players"
                shareKey="view"
                columns={[
                  {
                    key: "fav",
                    header: "Fav",
                    render: (row) => (
                      <button
                        aria-label={favorites.has(row.id) ? "Unfavorite" : "Favorite"}
                        onClick={() => toggleFav(row.id)}
                      >
                        <Star
                          className={`h-4 w-4 ${favorites.has(row.id) ? "text-yellow-500" : "text-gray-400"}`}
                          aria-hidden
                        />
                      </button>
                    ),
                  },
                  { key: "rank", header: "Rank", sortable: true },
                  { key: "name", header: "Name", sortable: true },
                  { key: "team", header: "Team", sortable: true },
                  { key: "pos", header: "Pos", sortable: true },
                  { key: "ppg", header: "PPG", sortable: true },
                  { key: "apg", header: "APG", sortable: true },
                  { key: "rpg", header: "RPG", sortable: true },
                ]}
              />
              <div className="mt-2 text-xs text-gray-600">
                Demo stats generated locally. Replace with API when available.
              </div>
            </div>
          </Card>
        </div>
      </div>
    </main>
  );
}
