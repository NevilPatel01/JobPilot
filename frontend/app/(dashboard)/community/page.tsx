import { MessageSquare, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/ui/PageHeader";

export default function CommunityPage() {
  return (
    <div>
      <PageHeader title="Community" description="Connect with other job seekers" />
      <div className="glass-panel flex flex-col items-center py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 ring-1 ring-indigo-500/20">
          <MessageSquare className="h-7 w-7 text-indigo-400" />
        </div>
        <h2 className="mt-5 text-xl font-semibold text-white">Coming in v0.2</h2>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-zinc-500">
          Forums and real-time chat rooms for interview prep, salary talk, and job search support.
        </p>
        <Link
          href="https://github.com/NevilPatel01/JobPilot/blob/main/ROADMAP.md"
          target="_blank"
          className="btn-secondary mt-6"
        >
          View Roadmap
          <ArrowUpRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
