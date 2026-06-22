"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2 } from "lucide-react";
import type { Application } from "@/types";
import { KANBAN_COLUMNS } from "@/types";
import { cn } from "@/lib/utils";

interface ApplicationCardProps {
  app: Application;
  onUpdate: (id: string, data: Partial<Application>) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  isDragging?: boolean;
}

export function ApplicationCard({ app, onUpdate, onDelete, isDragging }: ApplicationCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: app.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "rounded-lg border border-border bg-background/80 p-3 transition-all duration-200 hover:border-border hover:shadow-lg hover:shadow-black/20",
        isDragging && "opacity-90 shadow-xl ring-1 ring-primary/25"
      )}
    >
      <div className="flex items-start gap-2">
        <button {...attributes} {...listeners} className="mt-0.5 cursor-grab text-muted-foreground/60 hover:text-muted-foreground">
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-foreground">{app.job_title}</p>
          <p className="truncate text-sm text-muted-foreground">{app.company}</p>
          {app.salary_range && (
            <span className="mt-1.5 inline-block rounded-md bg-amber-500/10 px-2 py-0.5 text-xs text-amber-400 ring-1 ring-amber-500/20">
              {app.salary_range}
            </span>
          )}
          {app.notes && <p className="mt-1.5 truncate text-xs text-muted-foreground">{app.notes}</p>}
          <select
            value={app.status}
            onChange={(e) => onUpdate(app.id, { status: e.target.value })}
            className="mt-2 w-full rounded-md border border-border bg-card px-2 py-1 text-xs text-muted-foreground focus:border-primary/50 focus:outline-none"
          >
            {KANBAN_COLUMNS.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={() => onDelete(app.id)}
          className="rounded p-1 text-muted-foreground/60 transition-colors hover:bg-red-500/10 hover:text-red-400"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
