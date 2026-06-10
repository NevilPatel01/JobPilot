export function SkeletonLoader({ count = 8 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex gap-4">
            <div className="h-8 w-8 rounded-lg bg-zinc-800" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/3 rounded bg-zinc-800" />
              <div className="h-3 w-1/4 rounded bg-zinc-800" />
              <div className="h-3 w-2/3 rounded bg-zinc-800" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
