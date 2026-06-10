"use client";

import { SessionProvider } from "next-auth/react";
import { AuthInit } from "./AuthInit";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <AuthInit />
      {children}
    </SessionProvider>
  );
}
