"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { getAuthToken, setAuthToken } from "@/lib/api";

export function AuthInit() {
  const { data: session } = useSession();

  useEffect(() => {
    if (session?.accessToken) {
      setAuthToken(session.accessToken);
    } else {
      getAuthToken();
    }
  }, [session?.accessToken]);

  return null;
}
