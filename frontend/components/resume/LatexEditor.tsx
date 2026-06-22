"use client";

import CodeMirror from "@uiw/react-codemirror";
import { oneDark } from "@codemirror/theme-one-dark";
import { latex } from "codemirror-lang-latex";

interface LatexEditorProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function LatexEditor({ value, onChange, className }: LatexEditorProps) {
  return (
    <CodeMirror
      value={value}
      height="100%"
      className={className}
      theme={oneDark}
      extensions={[latex()]}
      onChange={onChange}
      basicSetup={{
        lineNumbers: true,
        foldGutter: true,
        highlightActiveLine: true,
      }}
    />
  );
}
