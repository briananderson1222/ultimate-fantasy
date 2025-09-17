export default function Loading() {
  return (
    <div className="p-6" aria-busy>
      <div className="mx-auto max-w-3xl space-y-2">
        <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="h-4 w-64 animate-pulse rounded bg-gray-200" />
      </div>
    </div>
  );
}
