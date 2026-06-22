"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, ExternalLink, FileText, Upload, User } from "lucide-react";
import { api } from "@/lib/api";
import type { CoverLetterMeta, ResumeContent } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { cn } from "@/lib/utils";

type ParseFeedback = {
  warnings: string[];
  confidence: number;
  section_counts: Record<string, number>;
};

export default function CreateResumePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [companyUrl, setCompanyUrl] = useState("");
  const [sourceType, setSourceType] = useState<"profile" | "upload">("profile");
  const [uploadedContent, setUploadedContent] = useState<ResumeContent | null>(null);
  const [parseFeedback, setParseFeedback] = useState<ParseFeedback | null>(null);
  const [uploading, setUploading] = useState(false);
  const [createCoverLetter, setCreateCoverLetter] = useState(false);
  const [coverMeta, setCoverMeta] = useState<CoverLetterMeta>({});
  const [creating, setCreating] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setParseFeedback(null);
    try {
      const result = await api.uploadResumePdf(file);
      setUploadedContent(result.content);
      setParseFeedback({
        warnings: result.warnings,
        confidence: result.confidence,
        section_counts: result.section_counts,
      });
      setSourceType("upload");
    } catch (err) {
      console.error(err);
      alert(e instanceof Error ? e.message : "PDF upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleCreate = async () => {
    if (!title || !jobDescription) return;
    setCreating(true);
    try {
      const resume = await api.createResume({
        title,
        job_description: jobDescription,
        company_url: companyUrl || undefined,
        source_type: sourceType,
        content_json: sourceType === "upload" ? uploadedContent || undefined : undefined,
        create_cover_letter: createCoverLetter,
        cover_letter_meta: createCoverLetter ? coverMeta : undefined,
      });
      router.push(`/resumes/${resume.id}`);
    } catch (e) {
      console.error(e);
      alert("Failed to create resume. Check API keys in Settings.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <PageHeader title="Create a tailored resume" description="Paste the job description and we'll tailor your resume professionally." />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-muted-foreground">Resume Title</label>
            <input className="input-field mt-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Anthropic Software Engineer" />
          </div>

          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-muted-foreground">Job Description</label>
            <textarea className="input-field mt-1 min-h-[160px]" value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Paste the full job description..." />
          </div>

          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-muted-foreground">Company Website URL (optional)</label>
            <input className="input-field mt-1" value={companyUrl} onChange={(e) => setCompanyUrl(e.target.value)} placeholder="https://stripe.com" />
            <p className="mt-1 text-xs text-muted-foreground">We&apos;ll research this company to better tailor your resume.</p>
          </div>

          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-muted-foreground">Resume Source</label>
            <div className="mt-2 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setSourceType("profile")}
                className={cn("rounded-lg border p-4 text-left transition", sourceType === "profile" ? "border-primary bg-primary/10" : "border-border")}
              >
                <User className="h-5 w-5 text-primary" />
                <div className="mt-2 text-sm font-medium text-foreground">Use Profile</div>
                <div className="text-xs text-muted-foreground">From your saved profile data</div>
              </button>
              <label className={cn("cursor-pointer rounded-lg border p-4 text-left transition", sourceType === "upload" ? "border-primary bg-primary/10" : "border-border")}>
                <Upload className="h-5 w-5 text-primary" />
                <div className="mt-2 text-sm font-medium text-foreground">Upload Resume</div>
                <div className="text-xs text-muted-foreground">{uploading ? "Parsing PDF..." : "PDF upload"}</div>
                <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
              </label>
            </div>

            {parseFeedback && sourceType === "upload" && (
              <div className="mt-4 rounded-lg border border-border bg-card/50 p-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-medium uppercase tracking-widest text-primary">Parse quality</p>
                  <span
                    className={cn(
                      "text-xs font-medium",
                      parseFeedback.confidence >= 0.7
                        ? "text-emerald-400"
                        : parseFeedback.confidence >= 0.4
                          ? "text-amber-400"
                          : "text-red-400"
                    )}
                  >
                    {Math.round(parseFeedback.confidence * 100)}% confidence
                  </span>
                </div>

                <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                  {[
                    ["Experience", parseFeedback.section_counts.experience ?? 0],
                    ["Education", parseFeedback.section_counts.education ?? 0],
                    ["Projects", parseFeedback.section_counts.projects ?? 0],
                    ["Skills", parseFeedback.section_counts.skill_categories ?? 0],
                    ["Summary", parseFeedback.section_counts.has_summary ?? 0],
                    ["Contact", parseFeedback.section_counts.has_contact_name ?? 0],
                  ].map(([label, count]) => (
                    <div key={String(label)} className="rounded border border-border px-2 py-2">
                      <div className="text-lg font-semibold text-foreground">{count as number}</div>
                      <div className="text-muted-foreground">{label as string}</div>
                    </div>
                  ))}
                </div>

                {parseFeedback.warnings.length > 0 && (
                  <ul className="mt-3 space-y-1 text-xs text-amber-300/90">
                    {parseFeedback.warnings.map((warning) => (
                      <li key={warning} className="flex gap-2">
                        <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                        <span>{warning}</span>
                      </li>
                    ))}
                  </ul>
                )}

                <Link
                  href="/profile"
                  className="btn-secondary mt-4 inline-flex w-full justify-center text-xs"
                >
                  <ExternalLink className="h-3 w-3" /> Review parsed sections in profile
                </Link>
              </div>
            )}
          </div>

          <div className="glass-panel p-4">
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input type="checkbox" checked={createCoverLetter} onChange={(e) => setCreateCoverLetter(e.target.checked)} className="rounded" />
              Also create cover letter
            </label>
            {createCoverLetter && (
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <input className="input-field" placeholder="Hiring manager name" value={coverMeta.hiring_manager_name || ""} onChange={(e) => setCoverMeta({ ...coverMeta, hiring_manager_name: e.target.value })} />
                <input className="input-field" placeholder="Hiring manager email" value={coverMeta.hiring_manager_email || ""} onChange={(e) => setCoverMeta({ ...coverMeta, hiring_manager_email: e.target.value })} />
                <input className="input-field sm:col-span-2" placeholder="Street address" value={coverMeta.street_address || ""} onChange={(e) => setCoverMeta({ ...coverMeta, street_address: e.target.value })} />
                <input className="input-field" placeholder="City" value={coverMeta.city || ""} onChange={(e) => setCoverMeta({ ...coverMeta, city: e.target.value })} />
                <input className="input-field" placeholder="State / province" value={coverMeta.state_province || ""} onChange={(e) => setCoverMeta({ ...coverMeta, state_province: e.target.value })} />
                <input className="input-field" placeholder="ZIP / postal code" value={coverMeta.postal_code || ""} onChange={(e) => setCoverMeta({ ...coverMeta, postal_code: e.target.value })} />
                <input className="input-field" type="date" value={coverMeta.letter_date || ""} onChange={(e) => setCoverMeta({ ...coverMeta, letter_date: e.target.value })} />
                <textarea className="input-field sm:col-span-2 min-h-[80px]" placeholder="Additional context (optional)" value={coverMeta.additional_context || ""} onChange={(e) => setCoverMeta({ ...coverMeta, additional_context: e.target.value })} />
              </div>
            )}
          </div>

          <button onClick={handleCreate} disabled={creating || !title || !jobDescription} className="btn-primary w-full py-3">
            {creating ? "Creating..." : createCoverLetter ? "Create Resume & Cover Letter" : "Create Resume"}
          </button>
        </div>

        <div className="glass-panel flex flex-col justify-center p-8">
          <FileText className="h-10 w-10 text-primary" />
          <p className="mt-4 text-sm font-medium text-foreground">Professional LaTeX resume</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Your resume is generated in Jake&apos;s Resume LaTeX style (Charter font, Font Awesome icons) and compiled to PDF with Tectonic.
            After creation you can edit the LaTeX source directly or refine structured sections — then export a polished PDF.
          </p>
          <ul className="mt-4 space-y-2 text-xs text-muted-foreground">
            <li>• AI tailoring updates structured content, then syncs LaTeX</li>
            <li>• Edit raw LaTeX for fine-grained formatting control</li>
            <li>• Live PDF preview in the editor</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
