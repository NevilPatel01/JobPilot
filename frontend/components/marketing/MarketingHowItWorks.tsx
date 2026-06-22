import Link from "next/link";
import { ArrowRight } from "lucide-react";

const steps = [
  { step: "01", title: "Set up your workspace", desc: "Add your profile, master resume, and private model key." },
  { step: "02", title: "Collect the right roles", desc: "Use Canadian sources or capture jobs manually as you browse." },
  { step: "03", title: "Apply with context", desc: "Tailor your documents and move every application through one tracker." },
];

export function MarketingHowItWorks() {
  return (
    <section className="border-t border-border/70 bg-card/30 py-24">
      <div className="mx-auto max-w-6xl px-6">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.18em] text-primary">The workflow</p>
        <h2 className="mt-3 text-center text-3xl font-semibold tracking-[-0.035em] text-foreground">From found to followed up</h2>
        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-border bg-border md:grid-cols-3">
          {steps.map(({ step, title, desc }) => (
            <div key={step} className="bg-card p-7 text-left">
              <span className="text-xs font-semibold tracking-[0.16em] text-primary">
                {step}
              </span>
              <h3 className="mt-8 font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{desc}</p>
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
