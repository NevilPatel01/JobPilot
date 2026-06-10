"use client";

import { signIn } from "next-auth/react";
import { Sparkles } from "lucide-react";

export default function LoginPage() {
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

  if (authDisabled) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="glass-panel w-full max-w-sm p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600/20 ring-1 ring-indigo-500/30">
            <Sparkles className="h-6 w-6 text-indigo-400" />
          </div>
          <h1 className="mt-5 text-xl font-semibold text-white">Dev Mode</h1>
          <p className="mt-2 text-sm text-zinc-500">Authentication is disabled for local development.</p>
          <a href="/" className="btn-primary mt-6 inline-flex w-full justify-center">
            Continue to Dashboard
          </a>
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

        <div className="mt-8 space-y-3">
          <button
            onClick={() => signIn("google", { callbackUrl: "/" })}
            className="btn-secondary w-full"
          >
            Sign in with Google
          </button>
          <button
            onClick={() => signIn("github", { callbackUrl: "/" })}
            className="btn-primary w-full"
          >
            Sign in with GitHub
          </button>
        </div>
      </div>
    </div>
  );
}
