import { CircleHelp } from "lucide-react";

export function ErrorState() {
  return (
    <section className="error-state" role="alert" aria-labelledby="error-title">
      <span className="error-icon"><CircleHelp size={25} aria-hidden="true" /></span>
      <div>
        <p className="section-kicker">Question not recognised</p>
        <h2 id="error-title">I couldn’t understand that question.</h2>
        <p>Include a supported location, parameter and time range, then try again.</p>
      </div>
    </section>
  );
}
