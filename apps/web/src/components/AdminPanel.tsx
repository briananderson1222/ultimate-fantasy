"use client";

import { useEffect, useMemo, useState } from "react";
import { Modal } from "./ui/modal";
import { Button } from "./ui/button";
import { ChevronDown, ChevronRight } from "lucide-react";

function b64urlEncode(input: Uint8Array | string): string {
  const bytes = typeof input === "string" ? new TextEncoder().encode(input) : input;
  let str = "";
  bytes.forEach((b) => (str += String.fromCharCode(b)));
  return btoa(str).replace(/=+/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

async function hmacSha256(key: string, data: string): Promise<string> {
  const enc = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    enc.encode(key),
    { name: "HMAC", hash: { name: "SHA-256" } },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", cryptoKey, enc.encode(data));
  return b64urlEncode(new Uint8Array(sig));
}

export default function AdminPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [devToolsExpanded, setDevToolsExpanded] = useState(false);
  const [secret, setSecret] = useState<string>("dev-secret");
  const [sub, setSub] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const [saved, setSaved] = useState<boolean>(false);

  // Only show in dev mode
  const isDev =
    process.env.NODE_ENV === "development" ||
    (typeof window !== "undefined" && window.location.hostname === "localhost");

  if (!isDev) return null;

  const randomUuid = useMemo(() => {
    return typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : "";
  }, []);

  useEffect(() => {
    if (!sub) setSub(randomUuid);
  }, [randomUuid, sub]);

  useEffect(() => {
    const stored = localStorage.getItem("uf_token");
    setSaved(!!stored);
  }, []);

  async function generateToken() {
    if (!sub || !secret) return;
    const header = { alg: "HS256", typ: "JWT" };
    const payload = { sub, email: "dev@example.com", name: "Dev User" };
    const headerB64 = b64urlEncode(JSON.stringify(header));
    const payloadB64 = b64urlEncode(JSON.stringify(payload));
    const toSign = `${headerB64}.${payloadB64}`;
    const signature = await hmacSha256(secret, toSign);
    const jwt = `${toSign}.${signature}`;
    setToken(jwt);
  }

  function saveToken() {
    if (!token) return;
    localStorage.setItem("uf_token", token);
    setSaved(true);
  }

  function clearToken() {
    localStorage.removeItem("uf_token");
    setSaved(false);
    setToken("");
  }

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="text-xs"
        title="Admin & Development Tools"
      >
        Admin
      </Button>

      <Modal open={isOpen} onClose={() => setIsOpen(false)} title="Admin Panel">
        <div className="space-y-6">
          {/* Admin Settings Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-[var(--color-text)] border-b border-[var(--border)] pb-2">
              Admin Settings
            </h3>
            <p className="text-sm text-[var(--color-muted)]">
              Administrative controls and league management options.
            </p>
            <div className="text-sm text-[var(--color-muted)] italic">
              Admin features coming soon...
            </div>
          </div>

          {/* Dev Tools Section - Collapsible */}
          <div className="space-y-4">
            <button
              onClick={() => setDevToolsExpanded(!devToolsExpanded)}
              className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text)] border-b border-[var(--border)] pb-2 w-full text-left hover:text-[var(--color-primary)]"
            >
              {devToolsExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              Development Tools
            </button>

            {devToolsExpanded && (
              <div className="space-y-4">
                <p className="text-sm text-[var(--color-muted)]">
                  Generate a development JWT token for testing authenticated endpoints.
                </p>

                <div>
                  <label className="block text-sm font-medium mb-1">User ID (sub)</label>
                  <input
                    type="text"
                    value={sub}
                    onChange={(e) => setSub(e.target.value)}
                    className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)]"
                    placeholder="User ID"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Secret</label>
                  <input
                    type="text"
                    value={secret}
                    onChange={(e) => setSecret(e.target.value)}
                    className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)]"
                    placeholder="dev-secret"
                  />
                </div>

                <div className="flex gap-2">
                  <Button onClick={generateToken}>Generate Token</Button>
                  {token && (
                    <Button onClick={saveToken} variant="secondary">
                      Save to Storage
                    </Button>
                  )}
                  {saved && (
                    <Button onClick={clearToken} variant="ghost">
                      Clear Token
                    </Button>
                  )}
                </div>

                {token && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Generated Token</label>
                    <textarea
                      value={token}
                      readOnly
                      className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] text-xs font-mono"
                      rows={3}
                    />
                  </div>
                )}

                {saved && (
                  <div className="text-sm text-green-600">
                    ✓ Token saved to localStorage as 'uf_token'
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Modal>
    </>
  );
}
