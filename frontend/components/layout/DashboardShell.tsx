"use client";

import Link from "next/link";
import { PanelLeft, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/layout/Sidebar";
import { SidebarProvider, useSidebar } from "@/components/layout/SidebarContext";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isOpen, open } = useSidebar();

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
          "min-h-screen px-5 py-7 transition-[margin-left] duration-300 ease-in-out sm:px-8 sm:py-9",
          isOpen ? "ml-60" : "ml-0"
        )}
      >
        <div className="mx-auto max-w-[1240px]">
          <div className="mb-5 flex items-center justify-end gap-2">
            <Link
              href="/settings"
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background/85 text-muted-foreground shadow-sm backdrop-blur transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Open settings"
              title="Settings"
            >
              <Settings className="h-4 w-4" />
            </Link>
            <ThemeToggle compact className="bg-background/85 shadow-sm backdrop-blur" />
          </div>
          {children}
        </div>
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
