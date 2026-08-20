import { MapPin } from "lucide-react";
import type { MapContext } from "../types/ocean";

export function OceanMap({ context }: { context: MapContext }) {
  return (
    <section className="map-card" aria-labelledby="location-title">
      <div className="panel-heading">
        <div><p className="section-kicker">Geographic context</p><h3 id="location-title">Indian Ocean region</h3></div>
        <span className="map-heading-icon"><MapPin size={16} aria-hidden="true" /></span>
      </div>
      <div className="map-visual">
        <img
          src="/bhuvan-3d-map.png"
          alt={`Bhuvan 3D satellite globe showing India and the Indian Ocean for ${context.label}, ${context.coordinates}`}
          loading="lazy"
          decoding="async"
        />
      </div>
      <div className="location-detail">
        <span className="mini-pin"><MapPin size={14} aria-hidden="true" /></span>
        <div><strong>{context.label}</strong><span>{context.coordinates}</span></div>
        <p>Bhuvan 3D overview • not for navigation</p>
      </div>
    </section>
  );
}
