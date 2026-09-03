import { useState } from "react";
import { useT } from "@/lib/i18n";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, FieldError } from "@/components/ui/Input";
import { useCreateMCPServer } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import type { MCPAuthType } from "@/lib/types";

export function AddMcpServerDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const t = useT();
  const [name, setName] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [authType, setAuthType] = useState<MCPAuthType>("none");
  const [headerName, setHeaderName] = useState("");
  const [secretValue, setSecretValue] = useState("");
  const [error, setError] = useState<string | undefined>();
  const create = useCreateMCPServer();
  const { push } = useToast();

  const reset = () => {
    setName("");
    setEndpoint("");
    setAuthType("none");
    setHeaderName("");
    setSecretValue("");
    setError(undefined);
  };

  const submit = () => {
    if (!name.trim() || !endpoint.trim()) {
      setError("Name and endpoint are required.");
      return;
    }
    if (authType === "header" && !headerName.trim()) {
      setError("Header name is required for header-based auth.");
      return;
    }
    setError(undefined);
    create.mutate(
      {
        name: name.trim(),
        endpoint: endpoint.trim(),
        auth_type: authType,
        header_name: authType === "header" ? headerName.trim() : null,
        secret_value: authType === "none" ? null : secretValue || null,
      },
      {
        onSuccess: () => {
          push({ tone: "success", title: "MCP server added", description: "Run Test connection to discover its capabilities." });
          reset();
          onClose();
        },
        onError: (err) => push({ tone: "error", title: "Failed to add server", description: (err as Error).message }),
      }
    );
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        reset();
        onClose();
      }}
      title={t("pages.integrations.addMcpServer")}
      description="Connect a remote MCP server over Streamable HTTP. Secrets are stored server-side and never sent to the browser again."
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" onClick={submit} loading={create.isPending}>
            Add server
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div>
          <Label htmlFor="mcp-name">{t("common.displayName")}</Label>
          <Input id="mcp-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="My tools server" />
        </div>
        <div>
          <Label htmlFor="mcp-endpoint">Endpoint URL</Label>
          <Input
            id="mcp-endpoint"
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            placeholder="https://mcp.example.com/rpc"
          />
        </div>
        <div>
          <Label htmlFor="mcp-auth">Authentication</Label>
          <Select id="mcp-auth" value={authType} onChange={(e) => setAuthType(e.target.value as MCPAuthType)}>
            <option value="none">{t("common.none")}</option>
            <option value="bearer">Bearer token</option>
            <option value="header">Custom header</option>
          </Select>
        </div>
        {authType === "header" && (
          <div>
            <Label htmlFor="mcp-header-name">Header name</Label>
            <Input id="mcp-header-name" value={headerName} onChange={(e) => setHeaderName(e.target.value)} placeholder="X-API-Key" />
          </div>
        )}
        {authType !== "none" && (
          <div>
            <Label htmlFor="mcp-secret">{authType === "bearer" ? "Bearer token" : "Header value"}</Label>
            <Input
              id="mcp-secret"
              type="password"
              autoComplete="off"
              value={secretValue}
              onChange={(e) => setSecretValue(e.target.value)}
              placeholder="Stored server-side only"
            />
          </div>
        )}
        <FieldError>{error}</FieldError>
      </div>
    </Dialog>
  );
}
