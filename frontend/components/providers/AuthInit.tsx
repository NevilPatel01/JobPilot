"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { getAuthToken, setAuthToken } from "@/lib/api";
import { authDisabled } from "@/lib/authFlags";

export function AuthInit() {
  const { data: session } = useSession();

  useEffect(() => {
    if (authDisabled) {
      setAuthToken(null);
      return;
    }

    if (session?.accessToken) {
      setAuthToken(session.accessToken);
    } else {
      getAuthToken();
    }
  }, [session?.accessToken]);

  return null;
}
