import Link from "next/link";
import { Navigation } from "lucide-react";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function MarketingNavbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-primary text-primary-foreground shadow-[0_8px_20px_hsl(var(--primary)/0.2)]">
            <Navigation className="h-4 w-4 fill-current" />
          </div>
          <span className="text-base font-semibold tracking-[-0.025em] text-foreground">JobPilot</span>
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
