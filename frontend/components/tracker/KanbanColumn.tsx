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
  to_apply: "border-t-primary/50",
  applied: "border-t-sky-500/50",
  interviewing: "border-t-amber-500/50",
  offer: "border-t-success/60",
  rejected: "border-t-red-500/50",
};

export function KanbanColumn({ id, label, count, onAdd, children }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col rounded-xl border border-border bg-card/60 backdrop-blur-sm",
        "border-t-2",
        columnAccents[id] || "border-t-border",
        isOver && "border-primary/40 bg-primary/5"
      )}
    >
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">{label}</span>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">{count}</span>
        </div>
        <button
          onClick={onAdd}
          className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          title="Add job"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      <div className="flex min-h-[420px] flex-col gap-2.5 px-3 pb-3">{children}</div>
    </div>
  );
}
