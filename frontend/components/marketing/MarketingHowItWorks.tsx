import Link from "next/link";
import { ArrowRight } from "lucide-react";

const steps = [
  { step: "1", title: "Sign in with GitHub", desc: "Secure OAuth — no passwords to manage." },
  { step: "2", title: "Add your LLM key", desc: "OpenAI or Claude with auto model selection for best cost." },
  { step: "3", title: "Paste a job & generate", desc: "AI researches the company and tailors your resume." },
];

export function MarketingHowItWorks() {
  return (
    <section className="border-t border-zinc-800/80 bg-zinc-900/30 py-16">
      <div className="mx-auto max-w-6xl px-6">
        <h2 className="text-center text-2xl font-semibold text-white">How it works</h2>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {steps.map(({ step, title, desc }) => (
            <div key={step} className="text-center">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600/20 text-lg font-semibold text-indigo-400 ring-1 ring-indigo-500/30">
                {step}
              </span>
              <h3 className="mt-4 font-medium text-white">{title}</h3>
              <p className="mt-2 text-sm text-zinc-500">{desc}</p>
            </div>
          ))}
        </div>
        <div className="mt-12 text-center">
          <Link href="/login" className="btn-primary inline-flex">
            Start for free
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
