import { cn } from "@/lib/utils";

export function MatchBadge({ score, keywords }: { score: number; keywords?: string[] }) {
  const color =
    score >= 60 ? "bg-indigo-600/20 text-indigo-400" : score >= 30 ? "bg-amber-500/20 text-amber-500" : "bg-red-500/20 text-red-500";

  return (
    <span
      className={cn("rounded-full px-2 py-0.5 text-xs font-medium", color)}
      title={keywords?.length ? `Matched: ${keywords.join(", ")}` : undefined}
    >
      {score}% match
    </span>
  );
}
