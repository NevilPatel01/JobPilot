/** JobPilot brand mark — folded paper plane climbing NE with an ascending trail.
 * Same artwork as app/icon.svg and public/logo*.svg; keep them in sync. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="10" fill="#0E7266" />
      <path d="M28 5.5 L8.2 16.8 L15.4 19.2 Z" fill="#FBF8EF" />
      <path d="M28 5.5 L15.4 19.2 L17.9 26.2 Z" fill="#5CD6C9" />
      <circle cx="6.6" cy="27.2" r="1.2" fill="#FBF8EF" opacity="0.55" />
      <circle cx="10.4" cy="23.6" r="1.6" fill="#FBF8EF" opacity="0.8" />
    </svg>
  );
}
