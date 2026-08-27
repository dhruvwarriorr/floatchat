import { CircleHelp } from "lucide-react";
import type { ChatApiError } from "../api/chatApi";

interface ErrorStateProps {
  errorInfo?: ChatApiError["error"] | null;
}

const titles: Record<string, string> = {
  parse_error: "I couldn’t understand that question.",
  no_data: "No observations were found.",
  general_error: "Something went wrong.",
};

export function ErrorState({ errorInfo }: ErrorStateProps) {
  const type = errorInfo?.type || "parse_error";
  const understood = errorInfo?.understood;
  const coordinates = understood?.latitude !== null && understood?.latitude !== undefined && understood?.longitude !== null && understood?.longitude !== undefined
    ? `${Math.abs(understood.latitude).toFixed(2)}°${understood.latitude >= 0 ? "N" : "S"}, ${Math.abs(understood.longitude).toFixed(2)}°${understood.longitude >= 0 ? "E" : "W"}`
    : null;
  return (
    <section className="error-state" role="alert" aria-labelledby="error-title">
      <span className="error-icon"><CircleHelp size={25} aria-hidden="true" /></span>
      <div>
        <p className="section-kicker">{type.replaceAll("_", " ")}</p>
        <h2 id="error-title">{titles[type] || titles.general_error}</h2>
        <p>{errorInfo?.message || "Include a supported location, parameter and time range, then try again."}</p>
        {errorInfo?.understanding && !understood && (
          <dl className="error-context">
            <div><dt>What I understood</dt><dd>{errorInfo.understanding}</dd></div>
          </dl>
        )}
        {understood && (
          <dl className="error-context">
            <div><dt>What I understood</dt><dd>{understood.location_label}{coordinates ? ` at ${coordinates}` : ""}; {understood.parameters.join(" and ")}; {understood.query_type.replaceAll("_", " ")}</dd></div>
            <div><dt>Date range</dt><dd>{understood.date_from} to {understood.date_to}{understood.calendar_month ? `; calendar month ${understood.calendar_month} only` : ""}{understood.season ? `; ${understood.season} months only` : ""}</dd></div>
            {errorInfo?.searched && <div><dt>What was searched</dt><dd>{errorInfo.searched}</dd></div>}
            {errorInfo?.records_found !== null && errorInfo?.records_found !== undefined && <div><dt>What was found</dt><dd>{errorInfo.records_found} matching records in the requested selection.</dd></div>}
            {errorInfo?.nearest_available_km !== null && errorInfo?.nearest_available_km !== undefined && <div><dt>Nearest available</dt><dd>Approximately {errorInfo.nearest_available_km.toFixed(0)} km from the query anchor.</dd></div>}
          </dl>
        )}
        {errorInfo?.suggestion && !errorInfo?.suggested_query && (
          <p className="error-suggestion">{errorInfo.suggestion}</p>
        )}
        {errorInfo?.suggested_query && <p className="error-query"><strong>Try this query:</strong> {errorInfo.suggested_query}</p>}
      </div>
    </section>
  );
}
