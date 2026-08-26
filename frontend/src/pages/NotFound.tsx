import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { EmptyState } from "@/components/ui/States";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <EmptyState
      icon={<Compass className="h-5 w-5" />}
      title="Page not found"
      description="This screen doesn't exist, or it moved."
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
