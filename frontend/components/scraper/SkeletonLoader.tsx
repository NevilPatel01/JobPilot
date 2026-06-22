export function SkeletonLoader({ count = 8 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-panel animate-pulse p-5">
          <div className="flex gap-4">
            <div className="h-10 w-10 shrink-0 rounded-xl bg-muted/80" />
            <div className="flex-1 space-y-3">
              <div className="h-4 w-2/5 rounded-md bg-muted/80" />
              <div className="h-3 w-1/4 rounded-md bg-muted/60" />
              <div className="h-3 w-3/4 rounded-md bg-muted/40" />
              <div className="flex gap-2 pt-1">
                <div className="h-7 w-20 rounded-lg bg-muted/60" />
                <div className="h-7 w-16 rounded-lg bg-muted/80" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
