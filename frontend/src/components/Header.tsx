import { Activity, Waves } from "lucide-react";

export function Header() {
  return (
    <header className="site-header">
      <div className="brand-lockup">
        <span className="brand-mark" aria-hidden="true"><Waves size={24} /></span>
        <div>
          <p className="brand-name">FloatChat-Lite</p>
          <p className="brand-tagline">Ask the Indian Ocean. Understand the answer.</p>
        </div>
      </div>
      <div className="header-actions">
        <nav className="header-nav" aria-label="Workspace navigation">
          <a href="#explore">Explore</a>
          <a href="#methodology">Methodology</a>
          <a href="#data-coverage">Data coverage</a>
        </nav>
        <span className="workflow-status"><Activity size={13} aria-hidden="true" /> Temperature • Salinity • Trends</span>
      </div>
    </header>
  );
}
