"use client";

import { useState } from "react";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Application } from "@/types";
import { KANBAN_COLUMNS } from "@/types";
import { KanbanColumn } from "./KanbanColumn";
import { ApplicationCard } from "./ApplicationCard";
import { AddJobModal, type CreateApplicationPayload } from "./AddJobModal";

interface KanbanBoardProps {
  applications: Application[];
  onUpdate: (id: string, data: Partial<Application>) => Promise<void>;
  onCreate: (data: CreateApplicationPayload) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function KanbanBoard({ applications, onUpdate, onCreate, onDelete }: KanbanBoardProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalStatus, setModalStatus] = useState("to_apply");

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const activeApp = applications.find((a) => a.id === activeId);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const appId = active.id as string;
    const newStatus = over.id as string;
    const app = applications.find((a) => a.id === appId);
    if (!app) return;

    const isColumn = KANBAN_COLUMNS.some((c) => c.id === newStatus);
    if (isColumn && app.status !== newStatus) {
      await onUpdate(appId, { status: newStatus });
    }
  };

  const openAddModal = (status: string) => {
    setModalStatus(status);
    setModalOpen(true);
  };

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {KANBAN_COLUMNS.map((col) => {
            const items = applications.filter((a) => a.status === col.id);
            return (
              <KanbanColumn
                key={col.id}
                id={col.id}
                label={col.label}
                count={items.length}
                onAdd={() => openAddModal(col.id)}
              >
                <SortableContext items={items.map((a) => a.id)} strategy={verticalListSortingStrategy}>
                  {items.map((app) => (
                    <ApplicationCard key={app.id} app={app} onUpdate={onUpdate} onDelete={onDelete} />
                  ))}
                </SortableContext>
              </KanbanColumn>
            );
          })}
        </div>
        <DragOverlay>
          {activeApp ? <ApplicationCard app={activeApp} onUpdate={onUpdate} onDelete={onDelete} isDragging /> : null}
        </DragOverlay>
      </DndContext>

      <AddJobModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        defaultStatus={modalStatus}
        onCreate={onCreate}
      />
    </>
  );
}
