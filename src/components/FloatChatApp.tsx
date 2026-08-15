import { ArrowRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { resolveOceanQuery } from "../data/oceanResponses";
import type { OceanResponse } from "../types/ocean";
import { ErrorState } from "./ErrorState";
import { Header } from "./Header";
import { LoadingSequence } from "./LoadingSequence";
import { QueryComposer } from "./QueryComposer";
import { ResultView } from "./ResultView";

const stages = ["Ask", "Interpret", "Analyse", "Explain"];
type ViewState = "idle" | "loading" | "success" | "error";

export function FloatChatApp() {
  const [query, setQuery] = useState("");
  const [view, setView] = useState<ViewState>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [response, setResponse] = useState<OceanResponse | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const timers = useRef<Array<ReturnType<typeof setTimeout>>>([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const scrollToOutput = () => {
    requestAnimationFrame(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  };

  const submit = () => {
    if (!query.trim() || view === "loading") return;
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setView("loading");
    setResponse(null);
    setActiveStep(0);
    scrollToOutput();

    timers.current.push(setTimeout(() => setActiveStep(1), 380));
    timers.current.push(setTimeout(() => setActiveStep(2), 760));
    timers.current.push(setTimeout(() => {
      const matched = resolveOceanQuery(query);
      setResponse(matched);
      setView(matched ? "success" : "error");
      scrollToOutput();
    }, 1180));
  };

  const reset = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setQuery("");
    setResponse(null);
    setView("idle");
    setActiveStep(0);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const selectFromError = (selected: string) => {
    setQuery(selected);
    setView("idle");
    setResponse(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const hasOutput = view !== "idle";

  return (
    <main className={`site-shell${hasOutput ? " has-output" : ""}`}>
      <div className="ambient-background" aria-hidden="true">
        <video
          className="background-video"
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          poster="/ocean-shore.avif"
        >
          <source src="/ocean-background.mp4" type="video/mp4" />
        </video>
        <div className="background-wash" />
      </div>

      <Header />
      <section className="hero" id="explore" aria-labelledby="hero-title">
        <div className="hero-copy-block">
          <p className="eyebrow">Indian Ocean analysis workspace</p>
          <h1 id="hero-title">Ask the ocean. See the pattern.</h1>
          <p className="hero-copy">Explore Indian Ocean temperature, salinity and long-term patterns through natural-language questions.</p>
        </div>

        <ol className="workflow" aria-label="How FloatChat-Lite works">
          {stages.map((stage, index) => (
            <li key={stage}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{stage}</strong>
              {index < stages.length - 1 && <ArrowRight size={14} aria-hidden="true" />}
            </li>
          ))}
        </ol>

        <QueryComposer
          query={query}
          onQueryChange={setQuery}
          onSubmit={submit}
          onReset={reset}
          isLoading={view === "loading"}
          hasResult={view === "success" || view === "error"}
        />
      </section>

      <div className="output-anchor" ref={outputRef}>
        {view === "loading" && <LoadingSequence activeStep={activeStep} />}
        {view === "success" && response && <ResultView response={response} />}
        {view === "error" && <ErrorState onSelect={selectFromError} />}
      </div>

      <footer>
        <span>FloatChat-Lite</span>
        <p>Indian Ocean intelligence • Local desktop experience</p>
      </footer>
    </main>
  );
}
