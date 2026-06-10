"use client";

import { useDroppable } from "@dnd-kit/core";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface KanbanColumnProps {
  id: string;
  label: string;
  count: number;
  onAdd: () => void;
  children: React.ReactNode;
}

const columnAccents: Record<string, string> = {
  to_apply: "border-t-indigo-500/50",
  applied: "border-t-sky-500/50",
  interviewing: "border-t-amber-500/50",
  offer: "border-t-emerald-500/50",
  rejected: "border-t-red-500/50",
};

export function KanbanColumn({ id, label, count, onAdd, children }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col rounded-xl border border-zinc-800/80 bg-zinc-900/60 backdrop-blur-sm",
        "border-t-2",
        columnAccents[id] || "border-t-zinc-700",
        isOver && "border-indigo-500/40 bg-indigo-600/5"
      )}
    >
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-200">{label}</span>
          <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium text-zinc-500">{count}</span>
        </div>
        <button
          onClick={onAdd}
          className="rounded-md p-1 text-zinc-600 transition-colors hover:bg-zinc-800 hover:text-indigo-400"
          title="Add job"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      <div className="flex min-h-[420px] flex-col gap-2.5 px-3 pb-3">{children}</div>
    </div>
  );
}
