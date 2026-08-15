import { Braces, Database, Layers3, Scale } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

export function ExplanationPanel({ response }: { response: OceanResponse }) {
  const items = [
    { icon: Braces, title: "What was calculated", copy: response.preparation.calculated },
    { icon: Layers3, title: "How values were grouped", copy: response.preparation.grouped },
    { icon: Database, title: "Baseline used", copy: response.preparation.baseline },
    { icon: Scale, title: "How to read the Z-score", copy: response.preparation.score },
  ];

  return (
    <section className="explanation-panel" id="methodology" aria-labelledby="explanation-title">
      <div className="explanation-heading">
        <div><p className="section-kicker">Transparent methodology</p><h2 id="explanation-title">How this answer was prepared</h2></div>
        <span>Calculation summary</span>
      </div>
      <p className="answer-explanation">{response.explanation}</p>
      <div className="preparation-grid">
        {items.map(({ icon: Icon, title, copy }) => (
          <article key={title}>
            <span><Icon size={15} aria-hidden="true" /></span>
            <div><h3>{title}</h3><p>{copy}</p></div>
          </article>
        ))}
      </div>
      {response.preparation.caveat && <p className="method-caveat"><strong>Measurement note</strong>{response.preparation.caveat}</p>}
      <p className="confidence-method"><strong>Confidence method</strong>Confidence is based on profile count: 1–5 Low, 6–20 Medium, and 21 or more High. This answer uses {response.profileCount} profiles.</p>
      <p className="disclosure">Displayed values are illustrative. The intended operational source is quality-controlled INCOIS ARGO data.</p>
    </section>
  );
}
