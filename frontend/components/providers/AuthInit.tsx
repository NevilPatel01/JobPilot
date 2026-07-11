"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { markAuthReady, setAuthToken } from "@/lib/api";
import { authDisabled } from "@/lib/authFlags";

export function AuthInit() {
  const { data: session, status } = useSession();

  useEffect(() => {
    if (authDisabled) {
      setAuthToken(null);
      markAuthReady();
      return;
    }

    // Do not let dashboard API calls race NextAuth session hydration. When
    // there is no session, also clear any token left over from an old backend
    // secret so the next request cannot fail with a misleading invalid-token
    // response.
    if (status === "loading") return;

    if (session?.accessToken) {
      setAuthToken(session.accessToken);
    } else {
      setAuthToken(null);
    }
    markAuthReady();
  }, [session?.accessToken, status]);

  return null;
}
