import { Suspense } from "react";
import { getAuthProviderFlags } from "@/lib/authFlags";
import { LoginClient } from "./LoginClient";

export default function LoginPage() {
  // Suspense boundary is required because LoginClient reads useSearchParams().
  return (
    <Suspense>
      <LoginClient {...getAuthProviderFlags()} />
    </Suspense>
  );
}
