import { MessageSquare } from "lucide-react";

export default function CommunityPage() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900 py-24">
      <MessageSquare className="h-12 w-12 text-indigo-400" />
      <h1 className="mt-4 text-2xl font-bold text-white">Community</h1>
      <p className="mt-2 max-w-md text-center text-sm text-zinc-400">
        Forums and real-time chat rooms are coming in v0.2.0. See the{" "}
        <a href="https://github.com/NevilPatel01/JobPilot/blob/main/ROADMAP.md" className="text-indigo-400 hover:underline">
          roadmap
        </a>{" "}
        for details.
      </p>
    </div>
  );
}
