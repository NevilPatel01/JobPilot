"use client";

/** A thin draggable vertical divider (xl screens only). Calls onResize with the
 *  horizontal delta in px as the user drags. */
export function ResizeHandle({ onResize }: { onResize: (deltaX: number) => void }) {
  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    let last = e.clientX;
    const move = (ev: MouseEvent) => {
      onResize(ev.clientX - last);
      last = ev.clientX;
    };
    const up = () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      onMouseDown={onMouseDown}
      className="hidden w-1.5 shrink-0 cursor-col-resize bg-border/40 transition-colors hover:bg-primary/50 xl:block"
    />
  );
}
