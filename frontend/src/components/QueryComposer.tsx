import { ArrowRight, RotateCcw, Sparkles } from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";
import { suggestedQueries } from "../data/suggestedQueries";

interface QueryComposerProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSubmit: () => void;
  onSuggestedClick: (query: string) => void;
  onReset: () => void;
  isLoading: boolean;
  hasResult: boolean;
}

export function QueryComposer({ query, onQueryChange, onSubmit, onSuggestedClick, onReset, isLoading, hasResult }: QueryComposerProps) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <div className="query-area">
      <form className="query-card" onSubmit={submit}>
        <label htmlFor="ocean-query"><Sparkles size={13} aria-hidden="true" /> Ask a question about the Indian Ocean</label>
        <div className="composer">
          <input
            id="ocean-query"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Ask about Indian Ocean temperature, salinity or trends…"
            aria-describedby="query-hint"
            disabled={isLoading}
            onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
              if (event.key === "Enter") {
                event.preventDefault();
                onSubmit();
              }
            }}
          />
          <button className="explore-button" type="submit" disabled={isLoading || !query.trim()}>
            {isLoading ? "Exploring" : "Explore"}<ArrowRight size={17} aria-hidden="true" />
          </button>
        </div>
        <div className="composer-meta">
          <p className="composer-hint" id="query-hint">Include a location, parameter and time range. Installed observations cover the Arabian Sea.</p>
          {hasResult && (
            <button type="button" className="reset-button" onClick={onReset}>
              <RotateCcw size={13} aria-hidden="true" /> Ask another question
            </button>
          )}
        </div>
        {!hasResult && !isLoading && (
          <div className="suggested-chips" aria-label="Suggested ocean questions">
            {suggestedQueries.map((suggestion) => (
              <button
                type="button"
                className="suggested-chip"
                key={suggestion}
                onClick={() => onSuggestedClick(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}
