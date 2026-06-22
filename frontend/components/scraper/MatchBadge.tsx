import { cn } from "@/lib/utils";

export function MatchBadge({ score, keywords }: { score: number; keywords?: string[] }) {
  const color =
    score >= 60
      ? "bg-primary/15 text-primary"
      : score >= 30
        ? "bg-amber-500/15 text-amber-700 dark:text-amber-400"
        : "bg-red-500/15 text-red-700 dark:text-red-400";

  return (
    <span
      className={cn("rounded-full px-2 py-0.5 text-xs font-medium", color)}
      title={keywords?.length ? `Matched: ${keywords.join(", ")}` : undefined}
    >
      {score}% match
    </span>
  );
}
