"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { KanbanBoard } from "@/components/tracker/KanbanBoard";

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
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Application Tracker</h1>
        <p className="text-sm text-zinc-400">Drag cards between columns or use the status dropdown</p>
      </div>
      <KanbanBoard
        applications={applications}
        onUpdate={handleUpdate}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
    </div>
  );
}
