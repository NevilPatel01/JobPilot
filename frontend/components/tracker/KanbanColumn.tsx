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

export function KanbanColumn({ id, label, count, onAdd, children }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col rounded-xl border border-zinc-800 bg-zinc-900",
        isOver && "border-indigo-600/50"
      )}
    >
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">{label}</span>
          <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">{count}</span>
        </div>
        <button
          onClick={onAdd}
          className="text-zinc-500 hover:text-indigo-400 transition-colors"
          title="Add job"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      <div className="flex min-h-[400px] flex-col gap-2 p-3">{children}</div>
    </div>
  );
}
