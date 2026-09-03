import { Link } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { Compass } from "lucide-react";
import { EmptyState } from "@/components/ui/States";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  const t = useT();
  return (
    <EmptyState
      icon={<Compass className="h-5 w-5" />}
      title={t("pages.notFound.title")}
      description={t("pages.notFound.description")}
      action={
        <Link to="/">
          <Button variant="outline" size="sm">
            Back to dashboard
          </Button>
        </Link>
      }
    />
  );
}
