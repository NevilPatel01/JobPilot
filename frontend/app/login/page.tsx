import { getAuthProviderFlags } from "@/lib/authFlags";
import { LoginClient } from "./LoginClient";

export default function LoginPage() {
  return <LoginClient {...getAuthProviderFlags()} />;
}
