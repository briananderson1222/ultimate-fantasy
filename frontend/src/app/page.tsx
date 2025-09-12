export default function HomePage() {
  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-4">
        <h1 className="text-2xl font-semibold">Ultimate Fantasy Platform</h1>
        <p className="text-gray-600">
          Next.js frontend scaffolded. Build pages in tasks T039–T040.
        </p>
        <ul className="list-disc pl-5 text-gray-700">
          <li>Leagues list and create pages</li>
          <li>Public league view and join</li>
          <li>Set lineup</li>
        </ul>
      </div>
    </main>
  );
}

