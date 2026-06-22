"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
  compact?: boolean;
}

export function ThemeToggle({ className, compact = false }: ThemeToggleProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <button
        type="button"
        className={cn(
          "flex items-center justify-center gap-2 rounded-lg border border-border bg-muted/50 text-sm text-muted-foreground",
          compact ? "h-9 w-9" : "w-full px-3 py-2",
          className
        )}
        aria-label="Toggle theme"
        disabled
      >
        <Sun className="h-4 w-4" />
        {!compact && "Theme"}
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "flex items-center justify-center gap-2 rounded-lg border border-border bg-muted/50 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
        compact ? "h-9 w-9" : "w-full px-3 py-2",
        className
      )}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={theme === "system" ? `System (${isDark ? "dark" : "light"})` : isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      {!compact && (isDark ? "Light mode" : "Dark mode")}
    </button>
  );
}
