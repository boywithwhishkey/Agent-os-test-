import { useState } from "react";
import { Check, Copy, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

export function CodeBlock({ code, language = "json" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="glass-ambient group relative overflow-hidden rounded-lg border border-hairline">
      <div className="flex items-center justify-between border-b border-hairline px-3 py-1.5">
        <span className="font-mono text-[10px] uppercase tracking-wider text-content-muted">{language}</span>
        <Button variant="ghost" size="sm" onClick={onCopy} className="h-6 px-2 text-xs">
          {copied ? <Check className="h-3 w-3 text-accent-green" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <pre className="max-h-96 overflow-auto p-3 font-mono text-xs leading-relaxed text-content-secondary">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export function JSONViewer({ data, collapsedByDefault = true }: { data: unknown; collapsedByDefault?: boolean }) {
  const [open, setOpen] = useState(!collapsedByDefault);
  const json = JSON.stringify(data, null, 2);
  return (
    <div className="rounded-lg border border-hairline">
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "focus-ring flex w-full items-center gap-1.5 rounded-t-lg px-3 py-2 text-xs font-medium text-content-secondary hover:bg-surface-hover",
          !open && "rounded-b-lg"
        )}
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        Raw JSON
      </button>
      {open && <CodeBlock code={json} />}
    </div>
  );
}
