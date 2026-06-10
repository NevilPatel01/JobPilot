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
  Rocket,
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
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-zinc-800 bg-zinc-900">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-5">
        <Rocket className="h-6 w-6 text-indigo-400" />
        <span className="text-lg font-bold text-white">JobPilot</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-indigo-600/20 text-indigo-400"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-800 p-4">
        {session?.user ? (
          <div className="flex items-center gap-3">
            {session.user.image && (
              <img src={session.user.image} alt="" className="h-8 w-8 rounded-full" />
            )}
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-white">{session.user.name}</p>
              <p className="truncate text-xs text-zinc-500">{session.user.email}</p>
            </div>
            <button
              onClick={() => signOut()}
              className="text-zinc-500 hover:text-zinc-300 transition-colors"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : authDisabled ? (
          <div className="text-xs text-zinc-500">Dev mode — auth disabled</div>
        ) : (
          <Link
            href="/login"
            className="block rounded-lg bg-indigo-600 px-3 py-2 text-center text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            Sign in
          </Link>
        )}
      </div>
    </aside>
  );
}
