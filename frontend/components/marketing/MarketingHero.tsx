import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function MarketingHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20 text-center">
      <p className="text-sm font-medium uppercase tracking-widest text-indigo-400">Open source · Self-hostable</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
        Your job search
        <span className="block text-indigo-400">command centre</span>
      </h1>
      <p className="mx-auto mt-6 max-w-2xl text-lg text-zinc-400">
        Scrape Canadian remote jobs, tailor resumes with AI, track applications on a Kanban board, and export
        professional LaTeX PDFs — all with your own API keys.
      </p>
      <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Link href="/login" className="btn-primary px-6 py-3 text-base">
          Sign in with GitHub
          <ArrowRight className="h-4 w-4" />
        </Link>
        <a
          href="https://github.com/NevilPatel01/JobPilot"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary px-6 py-3 text-base"
        >
          View on GitHub
        </a>
      </div>
    </section>
  );
}
