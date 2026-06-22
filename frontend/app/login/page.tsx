"use client";

import { signIn, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sparkles } from "lucide-react";
import Link from "next/link";
import { authDisabled, hasGithub, hasGoogle } from "@/lib/authFlags";

export default function LoginPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const noProviders = !hasGoogle && !hasGithub;

  useEffect(() => {
    if (status === "authenticated" && session) {
      router.replace("/dashboard");
    }
  }, [status, session, router]);

  if (authDisabled) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="glass-panel w-full max-w-sm p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600/20 ring-1 ring-indigo-500/30">
            <Sparkles className="h-6 w-6 text-indigo-400" />
          </div>
          <h1 className="mt-5 text-xl font-semibold text-white">Dev Mode</h1>
          <p className="mt-2 text-sm text-zinc-500">Authentication is disabled for local development.</p>
          <Link href="/dashboard" className="btn-primary mt-6 inline-flex w-full justify-center">
            Continue to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="glass-panel w-full max-w-sm p-8">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600/20 ring-1 ring-indigo-500/30">
            <Sparkles className="h-6 w-6 text-indigo-400" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight text-white">Welcome to JobPilot</h1>
          <p className="mt-2 text-sm text-zinc-500">Sign in to track applications and save jobs</p>
        </div>

        {noProviders ? (
          <p className="mt-8 text-center text-sm text-zinc-500">
            Configure GitHub OAuth in <code className="text-zinc-400">.env.local</code> to enable sign-in.
          </p>
        ) : (
          <div className="mt-8 space-y-3">
            {hasGithub && (
              <button onClick={() => signIn("github", { callbackUrl: "/dashboard" })} className="btn-primary w-full">
                Sign in with GitHub
              </button>
            )}
            {hasGoogle && (
              <button onClick={() => signIn("google", { callbackUrl: "/dashboard" })} className="btn-secondary w-full">
                Sign in with Google
              </button>
            )}
          </div>
        )}

        <p className="mt-6 text-center text-xs text-zinc-600">
          <Link href="/" className="hover:text-zinc-400">
            ← Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
