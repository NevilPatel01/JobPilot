import Link from "next/link";
import { Sparkles } from "lucide-react";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function MarketingNavbar() {
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/25">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <span className="text-base font-semibold tracking-tight text-foreground">JobPilot</span>
        </Link>
        <nav className="flex items-center gap-3">
          <ThemeToggle compact className="!w-9 border-border bg-muted/50" />
          <Link href="/login" className="btn-secondary text-sm">
            Sign in
          </Link>
          <Link href="/login" className="btn-primary text-sm">
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
