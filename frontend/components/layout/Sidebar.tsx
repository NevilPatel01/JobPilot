"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import {
  LayoutDashboard,
  Search,
  Columns3,
  User,
  BarChart3,
  MessageSquare,
  LogOut,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scraper", label: "Scraper", icon: Search },
  { href: "/tracker", label: "Tracker", icon: Columns3 },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/community", label: "Community", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-zinc-800/80 bg-zinc-900/95 backdrop-blur-xl">
      <div className="border-b border-zinc-800/80 px-5 py-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600/20 ring-1 ring-indigo-500/30">
            <Sparkles className="h-4 w-4 text-indigo-400" />
          </div>
          <div>
            <span className="text-base font-semibold tracking-tight text-white">JobPilot</span>
            <p className="text-[10px] font-medium uppercase tracking-widest text-zinc-600">Job Search OS</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-indigo-600/15 text-indigo-300 shadow-sm shadow-indigo-600/5 ring-1 ring-indigo-500/20"
                  : "text-zinc-500 hover:bg-zinc-800/60 hover:text-zinc-200"
              )}
            >
              <Icon className={cn("h-4 w-4", active && "text-indigo-400")} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-800/80 p-4">
        {session?.user ? (
          <div className="flex items-center gap-3 rounded-lg bg-zinc-800/40 p-2">
            {session.user.image && (
              <img src={session.user.image} alt="" className="h-8 w-8 rounded-full ring-2 ring-zinc-700" />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">{session.user.name}</p>
              <p className="truncate text-xs text-zinc-500">{session.user.email}</p>
            </div>
            <button
              onClick={() => signOut()}
              className="rounded-md p-1.5 text-zinc-500 transition-colors hover:bg-zinc-700 hover:text-zinc-300"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : authDisabled ? (
          <div className="rounded-lg bg-zinc-800/40 px-3 py-2 text-xs text-zinc-500">Dev mode</div>
        ) : (
          <Link href="/login" className="btn-primary w-full text-center">
            Sign in
          </Link>
        )}
      </div>
    </aside>
  );
}
