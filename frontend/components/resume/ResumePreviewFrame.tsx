"use client";

interface Props {
  html: string;
  className?: string;
}

export function ResumePreviewFrame({ html, className }: Props) {
  return (
    <iframe
      title="Resume preview"
      srcDoc={html}
      className={className || "h-full w-full rounded-lg border border-border bg-white"}
      sandbox="allow-same-origin"
    />
  );
}
