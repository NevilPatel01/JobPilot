"use client";

import { signIn } from "next-auth/react";
import { Rocket } from "lucide-react";

export default function LoginPage() {
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

  if (authDisabled) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950">
        <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-8 text-center">
          <Rocket className="mx-auto h-10 w-10 text-indigo-400" />
          <h1 className="mt-4 text-xl font-bold text-white">Dev Mode</h1>
          <p className="mt-2 text-sm text-zinc-400">Authentication is disabled. Go to the dashboard.</p>
          <a
            href="/"
            className="mt-6 inline-block rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            Continue to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950">
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-8">
        <div className="text-center">
          <Rocket className="mx-auto h-10 w-10 text-indigo-400" />
          <h1 className="mt-4 text-2xl font-bold text-white">Welcome to JobPilot</h1>
          <p className="mt-2 text-sm text-zinc-400">Sign in to track applications and save jobs</p>
        </div>

        <div className="mt-8 space-y-3">
          <button
            onClick={() => signIn("google", { callbackUrl: "/" })}
            className="flex w-full items-center justify-center gap-3 rounded-lg border border-zinc-700 bg-zinc-950 px-4 py-2.5 text-sm font-medium text-zinc-300 hover:border-zinc-600 hover:text-white transition-colors"
          >
            Sign in with Google
          </button>
          <button
            onClick={() => signIn("github", { callbackUrl: "/" })}
            className="flex w-full items-center justify-center gap-3 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            Sign in with GitHub
          </button>
        </div>
      </div>
    </div>
  );
}
