import { useState } from "react";
import { useT } from "@/lib/i18n";
import { KeyRound, Moon, Sun, Monitor, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { BrandMark } from "@/components/ui/BrandMark";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTheme } from "@/lib/theme";
import { useToast } from "@/components/ui/Toast";
import {
  DEFAULT_BASE_URL,
  getApiBaseUrl,
  getApiKey,
  isApiConfigured,
  resetApiConfig,
  setApiBaseUrl,
  setApiKey,
} from "@/lib/api/config";

export default function Settings() {
  const t = useT();
  const [baseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [apiKey, setApiKeyState] = useState(getApiKey());
  const [configured, setConfigured] = useState(isApiConfigured());
  const { theme, setTheme } = useTheme();
  const { push } = useToast();

  const save = () => {
    setApiBaseUrl(baseUrl.trim() || DEFAULT_BASE_URL);
    setApiKey(apiKey.trim());
    setConfigured(Boolean(apiKey.trim()));
    push({ tone: "success", title: "API configuration saved", description: "Stored for this browser tab only." });
  };

  const clear = () => {
    resetApiConfig();
    setBaseUrlState(DEFAULT_BASE_URL);
    setApiKeyState("");
    setConfigured(false);
    push({ tone: "info", title: "API configuration cleared" });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader
        title={t("pages.settings.title")}
        description={t("pages.settings.description")}
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-accent-gold" />
            {t("pages.settings.apiConnection")}
          </CardTitle>
          {configured ? (
            <Badge tone="green">
              <ShieldCheck className="h-3 w-3" /> Configured
            </Badge>
          ) : (
            <Badge tone="amber">{t("common.notConfigured")}</Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-content-secondary">{t("pages.settings.apiKeyNote")}</p>
          <div>
            <Label htmlFor="base-url">{t("pages.settings.apiBaseUrl")}</Label>
            <Input
              id="base-url"
              value={baseUrl}
              onChange={(e) => setBaseUrlState(e.target.value)}
              placeholder={DEFAULT_BASE_URL}
            />
          </div>
          <div>
            <Label htmlFor="api-key">{t("pages.settings.apiKeyLabel")}</Label>
            <Input
              id="api-key"
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(e) => setApiKeyState(e.target.value)}
              placeholder={t("pages.settings.apiKeyPlaceholder")}
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={save}>{t("common.saveConfiguration")}</Button>
            <Button variant="outline" onClick={clear}>
              {t("pages.settings.clear")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("common.appearance")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {(
              [
                // `value` is the stored theme token and never changes; the
                // label comes from the catalogue.
                { value: "dark", label: t("theme.dark"), icon: Moon },
                { value: "light", label: t("theme.light"), icon: Sun },
                { value: "system", label: t("theme.system"), icon: Monitor },
              ] as const
            ).map((option) => (
              <button
                key={option.value}
                onClick={() => setTheme(option.value)}
                className={`focus-ring flex flex-1 flex-col items-center gap-1.5 rounded-lg border p-3 text-sm font-medium transition-colors ${
                  theme === option.value
                    ? "border-accent-gold/40 bg-accent-gold/10 text-accent-gold"
                    : "border-hairline text-content-secondary hover:bg-surface-hover"
                }`}
              >
                <option.icon className="h-4 w-4" />
                {option.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("common.about")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center justify-between gap-3">
          <BrandMark variant="full" />
          <p className="text-xs text-content-muted">v0.1.0</p>
        </CardContent>
      </Card>
    </div>
  );
}
