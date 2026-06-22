import Link from "next/link";
import { Sparkles } from "lucide-react";

export function MarketingNavbar() {
  return (
    <header className="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600/20 ring-1 ring-indigo-500/30">
            <Sparkles className="h-4 w-4 text-indigo-400" />
          </div>
          <span className="text-base font-semibold tracking-tight text-white">JobPilot</span>
        </Link>
        <nav className="flex items-center gap-3">
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
