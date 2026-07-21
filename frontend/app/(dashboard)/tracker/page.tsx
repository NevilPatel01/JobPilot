"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { KanbanBoard } from "@/components/tracker/KanbanBoard";
import type { CreateApplicationPayload } from "@/components/tracker/AddJobModal";
import { PageHeader } from "@/components/ui/PageHeader";

export default function TrackerPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const load = useCallback(async (q?: string) => {
    try {
      const data = await api.getApplications(q);
      setApplications(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    load(query || undefined);
  }, [load, query]);

  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const handleUpdate = async (id: string, data: Partial<Application>) => {
    const updated = await api.updateApplication(id, data);
    setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  const handleCreate = async (data: CreateApplicationPayload) => {
    const { resumeFile, ...payload } = data;
    const created = await api.createApplication(payload);
    let finalApp = created;
    if (resumeFile) {
      finalApp = await api.uploadApplicationResume(created.id, resumeFile);
    }
    setApplications((prev) => [...prev, finalApp]);
  };

  const handleDelete = async (id: string) => {
    await api.deleteApplication(id);
    setApplications((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <div>
      <PageHeader
        title="Application Tracker"
        description="Log applications with JD and notes. Click a card to open full details."
      />
      <div className="mb-4">
        <label className="relative block max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title, company, notes, or job description…"
            className="input-field pl-9"
          />
        </label>
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
