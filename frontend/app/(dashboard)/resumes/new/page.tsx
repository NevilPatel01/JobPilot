"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, User } from "lucide-react";
import { api } from "@/lib/api";
import type { CoverLetterMeta, ResumeContent } from "@/types/resume";
import { emptyResumeContent } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { ResumePreviewFrame } from "@/components/resume/ResumePreviewFrame";
import { cn } from "@/lib/utils";
import { renderResumeHtmlClient } from "@/lib/resumePreview";

export default function CreateResumePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [companyUrl, setCompanyUrl] = useState("");
  const [sourceType, setSourceType] = useState<"profile" | "upload">("profile");
  const [uploadedContent, setUploadedContent] = useState<ResumeContent | null>(null);
  const [createCoverLetter, setCreateCoverLetter] = useState(false);
  const [coverMeta, setCoverMeta] = useState<CoverLetterMeta>({});
  const [previewHtml, setPreviewHtml] = useState("");
  const [creating, setCreating] = useState(false);
  const [profileContent, setProfileContent] = useState<ResumeContent>(emptyResumeContent());

  useEffect(() => {
    api.getStructuredProfile().then((p) => setProfileContent(p.content)).catch(console.error);
  }, []);

  const activeContent = sourceType === "upload" && uploadedContent ? uploadedContent : profileContent;

  useEffect(() => {
    setPreviewHtml(renderResumeHtmlClient(activeContent));
  }, [activeContent]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const result = await api.uploadResumePdf(file);
    setUploadedContent(result.content);
    setSourceType("upload");
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
      router.push("/resumes");
      router.refresh();
      void resume;
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
            <label className="text-xs font-medium text-zinc-400">Resume Title</label>
            <input className="input-field mt-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Anthropic Software Engineer" />
          </div>

          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-zinc-400">Job Description</label>
            <textarea className="input-field mt-1 min-h-[160px]" value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Paste the full job description..." />
          </div>

          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-zinc-400">Company Website URL (optional)</label>
            <input className="input-field mt-1" value={companyUrl} onChange={(e) => setCompanyUrl(e.target.value)} placeholder="https://stripe.com" />
            <p className="mt-1 text-xs text-zinc-600">We&apos;ll research this company to better tailor your resume.</p>
          </div>

          <div className="glass-panel p-4">
            <label className="text-xs font-medium text-zinc-400">Resume Source</label>
            <div className="mt-2 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setSourceType("profile")}
                className={cn("rounded-lg border p-4 text-left transition", sourceType === "profile" ? "border-indigo-500 bg-indigo-500/10" : "border-zinc-800")}
              >
                <User className="h-5 w-5 text-indigo-400" />
                <div className="mt-2 text-sm font-medium text-white">Use Profile</div>
                <div className="text-xs text-zinc-500">From your saved profile data</div>
              </button>
              <label className={cn("cursor-pointer rounded-lg border p-4 text-left transition", sourceType === "upload" ? "border-indigo-500 bg-indigo-500/10" : "border-zinc-800")}>
                <Upload className="h-5 w-5 text-indigo-400" />
                <div className="mt-2 text-sm font-medium text-white">Upload Resume</div>
                <div className="text-xs text-zinc-500">PDF upload</div>
                <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
              </label>
            </div>
          </div>

          <div className="glass-panel p-4">
            <label className="flex items-center gap-2 text-sm text-zinc-300">
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

        <div className="glass-panel p-4">
          <p className="text-xs font-medium uppercase tracking-widest text-indigo-400">Resume Preview</p>
          <div className="mt-3 h-[600px]">
            <ResumePreviewFrame html={previewHtml || "<html><body></body></html>"} />
          </div>
        </div>
      </div>
    </div>
  );
}
