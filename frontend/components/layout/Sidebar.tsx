"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import {
  LayoutDashboard,
  Search,
  Inbox,
  Columns3,
  User,
  BarChart3,
  MessageSquare,
  LogOut,
  Navigation,
  FileText,
  Mail,
  Plus,
  PanelLeftClose,
  Puzzle,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/components/layout/SidebarContext";

const primaryNavItems = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/inbox", label: "Job Inbox", icon: Inbox },
  { href: "/tracker", label: "Tracker", icon: Columns3 },
  { href: "/scraper", label: "Find Jobs", icon: Search },
  { href: "/resumes", label: "Resumes", icon: FileText },
  { href: "/profile", label: "User Profile", icon: User },
];

const secondaryNavItems = [
  { href: "/cover-letters", label: "Cover Letters", icon: Mail },
  { href: "/extension", label: "Chrome Capture", icon: Puzzle },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/community", label: "Community", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const { isOpen, close } = useSidebar();
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";
  const secondaryActive = secondaryNavItems.some(
    ({ href }) => pathname === href || pathname.startsWith(`${href}/`)
  );
  const [moreOpen, setMoreOpen] = useState(secondaryActive);

  const renderNavItem = ({ href, label, icon: Icon }: (typeof primaryNavItems)[number]) => {
    const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
    return (
      <Link
        key={href}
        href={href}
        className={cn(
          "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
          active
            ? "bg-primary/10 text-primary ring-1 ring-primary/15 before:absolute before:-left-0.5 before:h-4 before:w-0.5 before:rounded-full before:bg-primary"
            : "text-muted-foreground hover:bg-muted/80 hover:text-foreground"
        )}
      >
        <Icon className={cn("h-4 w-4", active && "text-primary")} />
        {label}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-sidebar-border/80 bg-sidebar/95 backdrop-blur-xl transition-transform duration-300 ease-in-out",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}
    >
      <div className="border-b border-sidebar-border px-5 py-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-primary text-primary-foreground shadow-[0_8px_20px_hsl(var(--primary)/0.2)]">
              <Navigation className="h-4 w-4 fill-current" />
            </div>
            <div className="min-w-0">
              <span className="text-base font-semibold tracking-[-0.025em] text-sidebar-foreground">JobPilot</span>
              <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">Career workspace</p>
            </div>
          </div>
          <button
            type="button"
            onClick={close}
            className="shrink-0 rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Close sidebar"
            title="Close sidebar"
          >
            <PanelLeftClose className="h-5 w-5" />
          </button>
        </div>
        <Link
          href="/resumes/new"
          className="btn-primary mt-4 flex w-full items-center justify-center gap-2 text-sm"
        >
          <Plus className="h-4 w-4" />
          New Resume
        </Link>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        {primaryNavItems.map(renderNavItem)}
        <button
          type="button"
          onClick={() => setMoreOpen((open) => !open)}
          className={cn(
            "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
            secondaryActive ? "text-primary" : "text-muted-foreground hover:bg-muted/80 hover:text-foreground"
          )}
        >
          <Plus className="h-4 w-4" />
          <span className="flex-1 text-left">More</span>
          <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", moreOpen && "rotate-180")} />
        </button>
        {moreOpen && <div className="space-y-0.5 border-l border-border/70 pl-2">{secondaryNavItems.map(renderNavItem)}</div>}
      </nav>

      <div className="space-y-3 border-t border-sidebar-border p-4">
        {session?.user ? (
          <div className="flex items-center gap-3 rounded-lg bg-muted/60 p-2">
            {session.user.image && (
              <Image
                src={session.user.image}
                alt=""
                width={32}
                height={32}
                unoptimized
                className="h-8 w-8 rounded-full ring-2 ring-border"
              />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">{session.user.name}</p>
              <p className="truncate text-xs text-muted-foreground">{session.user.email}</p>
            </div>
            <button
              onClick={() => signOut()}
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : authDisabled ? (
          <div className="rounded-lg bg-muted/60 px-3 py-2 text-xs text-muted-foreground">Dev mode</div>
        ) : (
          <Link href="/login" className="btn-primary w-full text-center">
            Sign in
          </Link>
        )}
      </div>
    </aside>
  );
}
