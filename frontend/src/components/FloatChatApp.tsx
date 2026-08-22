import { ArrowRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { adaptApiResponse } from "../api/adapter";
import { isErrorResponse, sendChatQuery } from "../api/chatApi";
import type { OceanResponse } from "../types/ocean";
import { ErrorState } from "./ErrorState";
import { Header } from "./Header";
import { LoadingSequence } from "./LoadingSequence";
import { QueryComposer } from "./QueryComposer";
import { ResultView } from "./ResultView";
import { ResultErrorBoundary } from "./ResultErrorBoundary";

const stages = ["Ask", "Interpret", "Analyse", "Explain"];
type ViewState = "idle" | "loading" | "success" | "error";
interface ErrorInfo {
  type: string;
  message: string;
  suggestion: string | null;
}

export function FloatChatApp() {
  const [query, setQuery] = useState("");
  const [view, setView] = useState<ViewState>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [response, setResponse] = useState<OceanResponse | null>(null);
  const [errorInfo, setErrorInfo] = useState<ErrorInfo | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const timers = useRef<Array<ReturnType<typeof setTimeout>>>([]);
  const requestId = useRef(0);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => {
    timers.current.forEach(clearTimeout);
    controller.current?.abort();
  }, []);

  const scrollToOutput = () => {
    requestAnimationFrame(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  };

  const submit = async (queryOverride?: string) => {
    const submittedQuery = (queryOverride ?? query).trim();
    if (!submittedQuery || view === "loading") return;
    timers.current.forEach(clearTimeout);
    timers.current = [];
    controller.current?.abort();
    controller.current = new AbortController();
    const activeRequest = ++requestId.current;
    if (queryOverride) setQuery(queryOverride);
    setView("loading");
    setResponse(null);
    setErrorInfo(null);
    setActiveStep(0);
    scrollToOutput();

    timers.current.push(setTimeout(() => setActiveStep(1), 300));
    timers.current.push(setTimeout(() => setActiveStep(2), 650));
    try {
      const result = await sendChatQuery(submittedQuery, controller.current.signal);
      if (activeRequest !== requestId.current) return;
      timers.current.forEach(clearTimeout);
      timers.current = [];
      setActiveStep(2);
      if (isErrorResponse(result)) {
        setErrorInfo(result.error);
        setView("error");
      } else {
        setResponse(adaptApiResponse(result));
        setView("success");
      }
      scrollToOutput();
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) {
        setErrorInfo({
          type: "general_error",
          message: "The response could not be prepared for display safely.",
          suggestion: "Please try again or ask a more specific question.",
        });
        setView("error");
      }
    }
  };

  const submitSuggested = (suggestion: string) => {
    void submit(suggestion);
  };

  const reset = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    requestId.current += 1;
    controller.current?.abort();
    setQuery("");
    setResponse(null);
    setErrorInfo(null);
    setView("idle");
    setActiveStep(0);
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
          onSubmit={() => void submit()}
          onSuggestedClick={submitSuggested}
          onReset={reset}
          isLoading={view === "loading"}
          hasResult={view === "success" || view === "error"}
        />
      </section>

      <div className="output-anchor" ref={outputRef}>
        {view === "loading" && <LoadingSequence activeStep={activeStep} />}
        {view === "success" && response && (
          <ResultErrorBoundary key={`${response.interpretedQuery}:${response.metadata.period}`}>
            <ResultView response={response} />
          </ResultErrorBoundary>
        )}
        {view === "error" && <ErrorState errorInfo={errorInfo} />}
      </div>

      <footer>
        <span>FloatChat-Lite</span>
        <p>Indian Ocean intelligence • Local desktop experience</p>
      </footer>
    </main>
  );
}
