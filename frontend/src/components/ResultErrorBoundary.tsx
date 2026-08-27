import { Component, type ReactNode } from "react";
import { ErrorState } from "./ErrorState";

interface Props {
  children: ReactNode;
}

interface State {
  failed: boolean;
}

/**
 * Keeps a chart, map, or lazy-chunk failure from unmounting the entire app.
 * The query composer remains available so the user never lands on a blank
 * background with no recovery path.
 */
export class ResultErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch() {
    console.error("FloatChat-Lite could not render this result safely.");
  }

  render() {
    if (this.state.failed) {
      return (
        <ErrorState
          errorInfo={{
            type: "general_error",
            message: "The answer arrived, but one of its visualizations could not be displayed.",
            suggestion: "Ask another question or refresh the page. The API and your key remain server-side.",
          }}
        />
      );
    }
    return this.props.children;
  }
}
