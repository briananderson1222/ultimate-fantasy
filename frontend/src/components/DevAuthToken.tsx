"use client";

import { useEffect, useMemo, useState } from "react";

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
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", cryptoKey, enc.encode(data));
  return b64urlEncode(new Uint8Array(sig));
}

export default function DevAuthToken() {
  const [secret, setSecret] = useState<string>("dev-secret");
  const [sub, setSub] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const [saved, setSaved] = useState<boolean>(false);
  const [showInfo, setShowInfo] = useState<boolean>(false);
  const [dismissed, setDismissed] = useState<boolean>(false);

  useEffect(() => {
    if (!sub && typeof crypto !== "undefined" && crypto.randomUUID) {
      setSub(crypto.randomUUID());
    }
  }, [sub]);

  const header = useMemo(() => ({ alg: "HS256", typ: "JWT" }), []);

  async function generate() {
    setSaved(false);
    const headerPart = b64urlEncode(JSON.stringify(header));
    const payloadPart = b64urlEncode(JSON.stringify({ sub }));
    const signingInput = `${headerPart}.${payloadPart}`;
    const signature = await hmacSha256(secret, signingInput);
    const t = `${signingInput}.${signature}`;
    setToken(t);
    try {
      localStorage.setItem("uf_token", t);
      setSaved(true);
    } catch {}
  }

  function clearToken() {
    try {
      localStorage.removeItem("uf_token");
    } catch {}
    setToken("");
    setSaved(false);
  }

  return (
    <div className="rounded border p-4 space-y-3">
      <h2 className="font-medium">Dev Auth Token</h2>
      {!dismissed && (
        <div className="rounded border border-yellow-200 bg-yellow-50 p-2 text-xs text-yellow-800 flex items-start justify-between gap-2">
          <div>
            Dev-only helper. Do not use in production.{' '}
            <button
              className="underline"
              onClick={() => setShowInfo((v) => !v)}
              type="button"
            >
              {showInfo ? 'Hide details' : 'Learn more'}
            </button>
            {' '}|{' '}
            <a
              className="underline"
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer noopener"
            >
              API Docs
            </a>
          </div>
          <button
            className="text-[11px] text-yellow-700 underline"
            onClick={() => {
              try { localStorage.setItem('uf_dev_auth_notice_dismissed', '1'); } catch {}
              setDismissed(true);
            }}
            type="button"
          >
            Dismiss
          </button>
        </div>
      )}
      {showInfo && (
        <div className="text-xs text-gray-700 space-y-2 bg-gray-50 rounded p-2">
          <p>
            Generates a JWT (HS256) in-browser and saves it to <code>localStorage.uf_token</code>.
            The frontend client sends it as <code>Authorization: Bearer &lt;token&gt;</code>.
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Subject (<code>sub</code>) is your user ID; defaults to a random UUID.</li>
            <li>Secret must match backend <code>AUTH_DEV_SECRET</code> (default <code>dev-secret</code>).</li>
            <li>Backend must run with <code>AUTH_MODE=dev</code>.</li>
          </ul>
        </div>
      )}
      <p className="text-xs text-gray-600">
        Generate and save a dev JWT (HS256) to <code>localStorage.uf_token</code>.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm text-gray-700">Subject (UUID)</label>
          <input
            value={sub}
            onChange={(e) => setSub(e.target.value)}
            placeholder="00000000-0000-0000-0000-000000000000"
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Secret</label>
          <input
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            placeholder="dev-secret"
            className="w-full rounded border px-3 py-2"
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          className="rounded bg-gray-800 px-3 py-2 text-white disabled:opacity-50"
          onClick={generate}
        >
          Generate & Save
        </button>
        <button className="rounded bg-red-100 px-3 py-2 text-red-700" onClick={clearToken}>
          Clear Token
        </button>
        {saved && <span className="text-xs text-green-700">Saved to localStorage</span>}
      </div>
      {token && (
        <div className="rounded bg-gray-50 p-2 text-xs break-all font-mono">
          {token}
        </div>
      )}
    </div>
  );
}
