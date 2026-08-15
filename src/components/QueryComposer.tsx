import { ArrowRight, RotateCcw, Sparkles } from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";
import { suggestedQueries } from "../data/oceanResponses";

interface QueryComposerProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSubmit: () => void;
  onReset: () => void;
  isLoading: boolean;
  hasResult: boolean;
}

export function QueryComposer({ query, onQueryChange, onSubmit, onReset, isLoading, hasResult }: QueryComposerProps) {
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
        <p className="composer-hint" id="query-hint">Choose a prompt below or ask using a location, parameter and time range.</p>
      </form>

      <div className="suggestions" aria-label="Suggested questions">
        <div className="suggestion-heading">
          <span>Suggested questions</span>
          {hasResult && (
            <button type="button" className="reset-button" onClick={onReset}>
              <RotateCcw size={13} aria-hidden="true" /> Ask another question
            </button>
          )}
        </div>
        <div className="chip-list">
          {suggestedQueries.map((suggestion) => (
            <button
              type="button"
              className={query === suggestion ? "query-chip selected" : "query-chip"}
              key={suggestion}
              onClick={() => onQueryChange(suggestion)}
              disabled={isLoading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
