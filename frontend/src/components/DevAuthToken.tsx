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
    <div className="rounded-lg border-2 border-dashed border-orange-300 bg-orange-50 p-4 space-y-4">
      <div className="flex items-center gap-2">
        <div className="bg-orange-500 text-white px-2 py-1 rounded text-xs font-semibold">DEV ONLY</div>
        <h2 className="font-semibold text-orange-900">Authentication Helper</h2>
      </div>
      
      {!dismissed && (
        <div className="rounded border border-orange-200 bg-orange-100 p-3 text-sm text-orange-800">
          <div className="flex items-start justify-between gap-2">
            <div>
              <strong>Development tool only!</strong> This generates fake authentication tokens for testing.
              <div className="mt-2 flex gap-4 text-xs">
                <button
                  className="underline hover:no-underline"
                  onClick={() => setShowInfo((v) => !v)}
                  type="button"
                >
                  {showInfo ? '▼ Hide instructions' : '▶ Show instructions'}
                </button>
                <a
                  className="underline hover:no-underline"
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  📖 API Docs
                </a>
              </div>
            </div>
            <button
              aria-label="Dismiss developer auth helper"
              className="text-xs text-orange-700 underline hover:no-underline"
              onClick={() => {
                try { localStorage.setItem('uf_dev_auth_notice_dismissed', '1'); } catch {}
                setDismissed(true);
              }}
              type="button"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {showInfo && (
        <div className="text-sm text-gray-700 space-y-3 bg-white rounded-lg p-4 border">
          <h3 className="font-medium text-gray-900">How to use:</h3>
          <ol className="list-decimal pl-5 space-y-2">
            <li>
              <strong>User ID:</strong> Enter the UUID of the user you want to authenticate as. 
              <br />
              <span className="text-xs text-gray-600">💡 Use the auto-generated UUID for a new user, or paste an existing user's ID</span>
            </li>
            <li>
              <strong>Secret:</strong> Must match your backend's <code className="bg-gray-100 px-1 rounded">AUTH_DEV_SECRET</code> 
              <br />
              <span className="text-xs text-gray-600">💡 Default is "dev-secret" - only change if you've customized your backend</span>
            </li>
            <li>
              <strong>Generate:</strong> Creates a JWT token and saves it to your browser's localStorage
              <br />
              <span className="text-xs text-gray-600">💡 The frontend will automatically use this token for API requests</span>
            </li>
          </ol>
          <div className="bg-blue-50 border border-blue-200 rounded p-2 text-xs">
            <strong>Troubleshooting:</strong> If you get 401 errors, make sure your backend is running with <code>AUTH_MODE=dev</code> and the secret matches.
          </div>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="dev-sub" className="mb-2 block text-sm font-medium text-gray-700">
            User ID (UUID) <span className="text-red-500">*</span>
          </label>
          <input
            id="dev-sub"
            value={sub}
            onChange={(e) => setSub(e.target.value)}
            placeholder="Auto-generated UUID"
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-600">This will be your user identity</p>
        </div>
        <div>
          <label htmlFor="dev-secret" className="mb-2 block text-sm font-medium text-gray-700">
            Backend Secret
          </label>
          <input
            id="dev-secret"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            placeholder="dev-secret"
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-600">Must match AUTH_DEV_SECRET</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="rounded bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={generate}
          disabled={!sub.trim()}
        >
          🔑 Generate & Save Token
        </button>
        <button 
          className="rounded bg-red-100 px-4 py-2 text-red-700 font-medium hover:bg-red-200" 
          onClick={clearToken}
        >
          🗑️ Clear Token
        </button>
        {saved && (
          <div className="flex items-center gap-1 text-sm text-green-700">
            <span>✅</span>
            <span>Token saved! You can now use the API.</span>
          </div>
        )}
      </div>

      {token && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Generated Token:</label>
          <div className="rounded bg-gray-100 p-3 text-xs break-all font-mono border">
            {token}
          </div>
          <p className="text-xs text-gray-600">
            💾 This token is automatically saved to localStorage and will be used for API requests.
          </p>
        </div>
      )}
    </div>
  );
}
