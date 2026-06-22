"use client";

import Link from "next/link";
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
  Sparkles,
  FileText,
  Mail,
  Settings,
  Plus,
  PanelLeftClose,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { HireMeButton } from "@/components/ui/HireMeButton";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useSidebar } from "@/components/layout/SidebarContext";

const navItems = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/profile", label: "User Profile", icon: User },
  { href: "/resumes", label: "My Resumes", icon: FileText },
  { href: "/cover-letters", label: "My Cover Letters", icon: Mail },
  { href: "/inbox", label: "Job Inbox", icon: Inbox },
  { href: "/scraper", label: "Canadian Jobs", icon: Search },
  { href: "/tracker", label: "Tracker", icon: Columns3 },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "API Settings", icon: Settings },
  { href: "/community", label: "Community", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const { isOpen, close } = useSidebar();
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-sidebar-border bg-sidebar/95 backdrop-blur-xl transition-transform duration-300 ease-in-out",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}
    >
      <div className="border-b border-sidebar-border px-5 py-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/25">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div className="min-w-0">
              <span className="text-base font-semibold tracking-tight text-sidebar-foreground">JobPilot</span>
              <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">Job Search OS</p>
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
          Create New
        </Link>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-primary/12 text-primary shadow-sm ring-1 ring-primary/20"
                  : "text-muted-foreground hover:bg-muted/80 hover:text-foreground"
              )}
            >
              <Icon className={cn("h-4 w-4", active && "text-primary")} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-3 border-t border-sidebar-border p-4">
        <ThemeToggle />
        <HireMeButton />
        {session?.user ? (
          <div className="flex items-center gap-3 rounded-lg bg-muted/60 p-2">
            {session.user.image && (
              <img src={session.user.image} alt="" className="h-8 w-8 rounded-full ring-2 ring-border" />
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
