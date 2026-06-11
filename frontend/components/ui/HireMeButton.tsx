"use client";

import { Briefcase } from "lucide-react";

const HIRE_ME_URL =
  process.env.NEXT_PUBLIC_HIRE_ME_URL || "https://github.com/NevilPatel01";

export function HireMeButton({ className }: { className?: string }) {
  return (
    <a
      href={HIRE_ME_URL}
      target="_blank"
      rel="noopener noreferrer"
      className={
        className ||
        "flex w-full items-center justify-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-600/10 px-3 py-2.5 text-sm font-semibold text-emerald-300 transition hover:border-emerald-500/50 hover:bg-emerald-600/20 hover:text-emerald-200"
      }
    >
      <Briefcase className="h-4 w-4" />
      Hire Me
    </a>
  );
}
