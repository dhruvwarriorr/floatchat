import { Check, LoaderCircle } from "lucide-react";

const loadingSteps = [
  "Understanding your question",
  "Matching location and time range",
  "Preparing the visual explanation",
];

export function LoadingSequence({ activeStep }: { activeStep: number }) {
  return (
    <section className="loading-panel" aria-live="polite" aria-label="Preparing answer">
      <div className="loading-orb"><LoaderCircle size={23} aria-hidden="true" /></div>
      <div>
        <p className="loading-kicker">Building your ocean view</p>
        <ol className="loading-steps">
          {loadingSteps.map((step, index) => (
            <li className={index < activeStep ? "done" : index === activeStep ? "active" : ""} key={step}>
              <span>{index < activeStep ? <Check size={12} /> : index + 1}</span>{step}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
