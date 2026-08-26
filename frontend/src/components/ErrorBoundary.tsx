import { Component, type ReactNode } from "react";
import { AlertOctagon } from "lucide-react";
import { Button } from "./ui/Button";

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface-canvas p-6 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-red/10 text-accent-red">
            <AlertOctagon className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-semibold text-content-primary">The interface hit an unexpected error</p>
            <p className="mt-1 max-w-md text-sm text-content-muted">{this.state.error.message}</p>
          </div>
          <Button onClick={() => window.location.reload()}>Reload the app</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
