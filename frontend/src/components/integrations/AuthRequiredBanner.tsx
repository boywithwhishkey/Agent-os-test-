import { Link } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { Lock } from "lucide-react";

// Compact, honest, non-dominant — the catalog stays fully browsable below
// this. Never a full-page block: operator auth gates actions (connect,
// configure, test), not visibility of the catalog itself.
export function AuthRequiredBanner({ className }: { className?: string }) {
  const t = useT();
  return (
    <div
      className={`glass-soft flex flex-wrap items-center justify-between gap-3 rounded-xl border border-hairline px-4 py-2.5 text-sm text-content-secondary ${className ?? ""}`}
    >
      <span className="flex items-center gap-2.5">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-gold/10 text-accent-gold">
          <Lock className="h-3.5 w-3.5" />
        </span>
        {t("pages.integrations.operatorAccessRequired")}
      </span>
      <Link to="/settings" className="shrink-0 font-medium text-accent-gold hover:underline">
        {t("common.signIn")}
      </Link>
    </div>
  );
}
