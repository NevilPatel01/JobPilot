"use client";

import { PanelLeft } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/layout/Sidebar";
import { SidebarProvider, useSidebar } from "@/components/layout/SidebarContext";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

// Full-bleed, app-like pages that manage their own height/scroll (the resume
// editor). They get no page padding or max-width so they can use the full
// viewport — and reclaim the sidebar's space when it is collapsed.
function isFullBleedRoute(pathname: string): boolean {
  return pathname !== "/resumes/new" && /^\/resumes\/[^/]+$/.test(pathname);
}

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isOpen, open } = useSidebar();
  const pathname = usePathname();
  const fullBleed = isFullBleedRoute(pathname || "");

  return (
    <div className="min-h-screen">
      <Sidebar />
      {!isOpen && (
        <button
          type="button"
          onClick={open}
          className="fixed left-4 top-4 z-50 flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background/95 text-muted-foreground shadow-sm backdrop-blur transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Open sidebar"
          title="Open sidebar"
        >
          <PanelLeft className="h-5 w-5" />
        </button>
      )}
      <main
        className={cn(
          "transition-[margin-left] duration-300 ease-in-out",
          isOpen ? "ml-60" : "ml-0",
          fullBleed ? "h-screen overflow-hidden" : "min-h-screen px-5 py-7 sm:px-8 sm:py-9"
        )}
      >
        {fullBleed ? (
          children
        ) : (
          <div className="mx-auto max-w-[1240px]">
            <div className="mb-5 flex items-center justify-end gap-2">
              <ThemeToggle compact className="bg-background/85 shadow-sm backdrop-blur" />
            </div>
            {children}
          </div>
        )}
      </main>
    </div>
  );
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <DashboardContent>{children}</DashboardContent>
    </SidebarProvider>
  );
}
