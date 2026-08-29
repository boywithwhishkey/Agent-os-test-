import { useEffect, useState } from "react";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, Textarea, FieldError } from "@/components/ui/Input";
import type { StepType, WorkflowStep } from "@/lib/types";

interface StepEditorDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (step: WorkflowStep) => void;
  initial?: WorkflowStep;
  existingIds: string[];
}

export function StepEditorDialog({ open, onClose, onSave, initial, existingIds }: StepEditorDialogProps) {
  const [id, setId] = useState("");
  const [type, setType] = useState<StepType>("noop");
  const [inputText, setInputText] = useState("{}");
  const [maxRetries, setMaxRetries] = useState(0);
  const [timeoutSeconds, setTimeoutSeconds] = useState(30);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    if (!open) return;
    setId(initial?.id ?? `step-${existingIds.length + 1}`);
    setType(initial?.type ?? "noop");
    setInputText(JSON.stringify(initial?.input ?? {}, null, 2));
    setMaxRetries(initial?.max_retries ?? 0);
    setTimeoutSeconds(initial?.timeout_seconds ?? 30);
    setError(undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initial]);

  const save = () => {
    if (!id.trim()) {
      setError("Step id is required");
      return;
    }
    if (!initial && existingIds.includes(id.trim())) {
      setError("Step id must be unique");
      return;
    }
    let input: Record<string, unknown>;
    try {
      input = inputText.trim() ? JSON.parse(inputText) : {};
    } catch {
      setError("Input must be valid JSON");
      return;
    }
    onSave({
      id: id.trim(),
      type,
      depends_on: initial?.depends_on ?? [],
      input,
      condition_key: initial?.condition_key ?? null,
      condition_equals: initial?.condition_equals,
      max_retries: maxRetries,
      timeout_seconds: timeoutSeconds,
    });
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={initial ? "Edit step" : "Add step"}
      description="Connect steps on the canvas to set dependencies."
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" onClick={save}>
            Save step
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <Label htmlFor="step-id">Step ID</Label>
            <Input id="step-id" value={id} onChange={(e) => setId(e.target.value)} disabled={Boolean(initial)} />
          </div>
          <div>
            <Label htmlFor="step-type">Type</Label>
            <Select id="step-type" value={type} onChange={(e) => setType(e.target.value as StepType)}>
              <option value="noop">No-op</option>
              <option value="tool">Tool</option>
              <option value="agent">Agent</option>
              <option value="integration">Integration</option>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <Label htmlFor="max-retries">Max retries</Label>
            <Input
              id="max-retries"
              type="number"
              min={0}
              max={10}
              value={maxRetries}
              onChange={(e) => setMaxRetries(Number(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="timeout">Timeout (seconds)</Label>
            <Input
              id="timeout"
              type="number"
              min={1}
              max={3600}
              value={timeoutSeconds}
              onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
            />
          </div>
        </div>
        <div>
          <Label htmlFor="step-input">Input (JSON)</Label>
          <Textarea id="step-input" value={inputText} onChange={(e) => setInputText(e.target.value)} rows={5} className="font-mono text-xs" />
        </div>
        <FieldError>{error}</FieldError>
      </div>
    </Dialog>
  );
}
