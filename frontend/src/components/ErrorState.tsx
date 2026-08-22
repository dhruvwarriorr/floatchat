import { CircleHelp } from "lucide-react";

interface ErrorStateProps {
  errorInfo?: { type: string; message: string; suggestion: string | null } | null;
}

const titles: Record<string, string> = {
  parse_error: "I couldn’t understand that question.",
  no_data: "No observations were found.",
  general_error: "Something went wrong.",
};

export function ErrorState({ errorInfo }: ErrorStateProps) {
  const type = errorInfo?.type || "parse_error";
  return (
    <section className="error-state" role="alert" aria-labelledby="error-title">
      <span className="error-icon"><CircleHelp size={25} aria-hidden="true" /></span>
      <div>
        <p className="section-kicker">{type.replaceAll("_", " ")}</p>
        <h2 id="error-title">{titles[type] || titles.general_error}</h2>
        <p>{errorInfo?.message || "Include a supported location, parameter and time range, then try again."}</p>
        {errorInfo?.suggestion && <p className="error-suggestion">{errorInfo.suggestion}</p>}
      </div>
    </section>
  );
}
