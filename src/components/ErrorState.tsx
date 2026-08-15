import { CircleHelp, CornerDownRight } from "lucide-react";
import { suggestedQueries } from "../data/oceanResponses";

export function ErrorState({ onSelect }: { onSelect: (query: string) => void }) {
  return (
    <section className="error-state" role="alert" aria-labelledby="error-title">
      <span className="error-icon"><CircleHelp size={25} aria-hidden="true" /></span>
      <div>
        <p className="section-kicker">Let’s try a supported view</p>
        <h2 id="error-title">I couldn’t understand that question. Try: “Show temperature profile near Mumbai in July 2024.”</h2>
        <p>Try one of these working questions, then press Explore:</p>
        <div className="error-suggestions">
          {suggestedQueries.slice(0, 2).map((query) => (
            <button key={query} type="button" onClick={() => onSelect(query)}><CornerDownRight size={14} aria-hidden="true" />{query}</button>
          ))}
        </div>
      </div>
    </section>
  );
}
