"use client";

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface PdfPreviewPaneProps {
  pdfUrl: string | null;
  loading: boolean;
  error: string | null;
  className?: string;
}

export function PdfPreviewPane({ pdfUrl, loading, error, className }: PdfPreviewPaneProps) {
  return (
    <div className={cn("flex h-full flex-col overflow-hidden rounded-lg border border-zinc-800 bg-white", className)}>
      {loading && (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 text-xs text-zinc-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          Compiling LaTeX to PDF...
        </div>
      )}
      {!loading && error && (
        <div className="flex flex-1 items-center justify-center p-4 text-center text-xs text-red-600">{error}</div>
      )}
      {!loading && !error && pdfUrl && (
        <iframe title="LaTeX PDF preview" src={pdfUrl} className="h-full w-full" />
      )}
      {!loading && !error && !pdfUrl && (
        <div className="flex flex-1 items-center justify-center p-4 text-center text-xs text-zinc-500">
          PDF preview will appear after LaTeX compiles.
        </div>
      )}
    </div>
  );
}
