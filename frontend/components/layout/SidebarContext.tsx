"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

const STORAGE_KEY = "jobpilot-sidebar-open";

type SidebarContextValue = {
  isOpen: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
};

const SidebarContext = createContext<SidebarContextValue | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(true);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored !== null) setIsOpen(stored === "true");
    setHydrated(true);
  }, []);

  const persist = useCallback((open: boolean) => {
    setIsOpen(open);
    localStorage.setItem(STORAGE_KEY, String(open));
  }, []);

  const toggle = useCallback(() => persist(!isOpen), [isOpen, persist]);
  const open = useCallback(() => persist(true), [persist]);
  const close = useCallback(() => persist(false), [persist]);

  return (
    <SidebarContext.Provider value={{ isOpen: hydrated ? isOpen : true, toggle, open, close }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider");
  return ctx;
}
