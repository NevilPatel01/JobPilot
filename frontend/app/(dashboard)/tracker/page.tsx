"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { KanbanBoard } from "@/components/tracker/KanbanBoard";
import { PageHeader } from "@/components/ui/PageHeader";

export default function TrackerPage() {
  const [applications, setApplications] = useState<Application[]>([]);

  const load = useCallback(async () => {
    try {
      const data = await api.getApplications();
      setApplications(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleUpdate = async (id: string, data: Partial<Application>) => {
    const updated = await api.updateApplication(id, data);
    setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  const handleCreate = async (data: Partial<Application>) => {
    const created = await api.createApplication(data);
    setApplications((prev) => [...prev, created]);
  };

  const handleDelete = async (id: string) => {
    await api.deleteApplication(id);
    setApplications((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <div>
      <PageHeader
        title="Application Tracker"
        description="Drag cards between columns or use the status dropdown"
      />
      <KanbanBoard
        applications={applications}
        onUpdate={handleUpdate}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
    </div>
  );
}
