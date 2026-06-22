"use client";

import { Plus, Trash2 } from "lucide-react";
import type { CoverLetterContent, CoverLetterDocument } from "@/types/resume";

type Props = {
  letter: CoverLetterDocument;
  content: CoverLetterContent;
  onContentChange: (content: CoverLetterContent) => void;
  onMetaChange: (updates: Partial<CoverLetterDocument>) => void;
};

function field(label: string, value: string, onChange: (v: string) => void, placeholder?: string) {
  return (
    <div>
      <label className="text-xs text-muted-foreground">{label}</label>
      <input
        className="input-field mt-1 text-sm"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export function CoverLetterStructuredEditor({ letter, content, onContentChange, onMetaChange }: Props) {
  const updateContent = (patch: Partial<CoverLetterContent>) => {
    onContentChange({ ...content, ...patch });
  };

  const updateParagraph = (index: number, text: string) => {
    const paragraphs = [...content.paragraphs];
    paragraphs[index] = text;
    updateContent({ paragraphs });
  };

  const addParagraph = () => {
    updateContent({ paragraphs: [...content.paragraphs, ""] });
  };

  const removeParagraph = (index: number) => {
    updateContent({ paragraphs: content.paragraphs.filter((_, i) => i !== index) });
  };

  const wordCount = content.paragraphs.join(" ").split(/\s+/).filter(Boolean).length;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xs font-medium uppercase tracking-widest text-primary">Header</h2>
        <div className="mt-3 space-y-3">
          {field("Hiring manager", letter.hiring_manager_name || "", (v) => {
            onMetaChange({ hiring_manager_name: v });
            updateContent({ recipient_name: v, salutation: v ? `Dear ${v},` : "Dear Hiring Manager," });
          })}
          {field("Company", content.company_name, (v) => updateContent({ company_name: v }))}
          {field("Street address", letter.street_address || "", (v) => onMetaChange({ street_address: v }))}
          <div className="grid grid-cols-2 gap-2">
            {field("City", letter.city || "", (v) => onMetaChange({ city: v }))}
            {field("State / Province", letter.state_province || "", (v) => onMetaChange({ state_province: v }))}
          </div>
          {field("Postal code", letter.postal_code || "", (v) => onMetaChange({ postal_code: v }))}
          {field("Date", content.date, (v) => {
            onMetaChange({ letter_date: v });
            updateContent({ date: v });
          })}
          {field("Salutation", content.salutation, (v) => updateContent({ salutation: v }))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-medium uppercase tracking-widest text-primary">Body</h2>
          <span className={`text-xs ${wordCount >= 250 && wordCount <= 400 ? "text-emerald-400" : "text-amber-400"}`}>
            {wordCount} words {wordCount < 250 ? "(aim for 250–400)" : wordCount > 400 ? "(over limit)" : ""}
          </span>
        </div>
        <div className="mt-3 space-y-3">
          {content.paragraphs.map((para, idx) => (
            <div key={idx} className="relative">
              <label className="text-xs text-muted-foreground">Paragraph {idx + 1}</label>
              <textarea
                className="input-field mt-1 min-h-[100px] text-sm"
                value={para}
                onChange={(e) => updateParagraph(idx, e.target.value)}
              />
              {content.paragraphs.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeParagraph(idx)}
                  className="absolute right-2 top-7 text-muted-foreground hover:text-red-400"
                  aria-label="Remove paragraph"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addParagraph} className="btn-secondary w-full text-xs">
            <Plus className="h-3 w-3" /> Add paragraph
          </button>
        </div>
      </div>

      <div>
        {field("Closing", content.closing, (v) => updateContent({ closing: v }))}
      </div>

      <div>
        <label className="text-xs text-muted-foreground">Additional context (for AI regeneration)</label>
        <textarea
          className="input-field mt-1 min-h-[60px] text-sm"
          value={letter.additional_context || ""}
          onChange={(e) => onMetaChange({ additional_context: e.target.value })}
          placeholder="Referral name, relocation, visa status..."
        />
      </div>
    </div>
  );
}
