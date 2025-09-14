"use client";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="p-6">
      <div className="mx-auto max-w-3xl rounded border bg-red-50 p-4 text-red-800">
        <p className="font-medium">Something went wrong</p>
        <p className="text-sm">{error.message}</p>
        <button className="mt-3 rounded bg-red-700 px-3 py-1 text-white" onClick={reset}>Try again</button>
      </div>
    </div>
  );
}

