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
        "rounded-xl border border-zinc-800 bg-zinc-950 p-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-zinc-700",
        isDragging && "opacity-80 shadow-lg"
      )}
    >
      <div className="flex items-start gap-2">
        <button {...attributes} {...listeners} className="mt-0.5 text-zinc-600 hover:text-zinc-400 cursor-grab">
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-white truncate">{app.job_title}</p>
          <p className="text-sm text-zinc-400 truncate">{app.company}</p>
          {app.salary_range && (
            <span className="mt-1 inline-block rounded-md bg-amber-500/20 px-2 py-0.5 text-xs text-amber-500">
              {app.salary_range}
            </span>
          )}
          {app.notes && <p className="mt-1 text-xs text-zinc-500 truncate">{app.notes}</p>}
          <select
            value={app.status}
            onChange={(e) => onUpdate(app.id, { status: e.target.value })}
            className="mt-2 w-full rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-400 focus:border-indigo-600 focus:outline-none"
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
          className="text-zinc-600 hover:text-red-500 transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
