"use client";

import { SessionProvider } from "next-auth/react";
import { AuthInit } from "./AuthInit";
import { ThemeProvider } from "./ThemeProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <SessionProvider>
        <AuthInit />
        {children}
      </SessionProvider>
    </ThemeProvider>
  );
}
