import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/manrope";
import "@fontsource-variable/space-grotesk";
import "leaflet/dist/leaflet.css";
import { FloatChatApp } from "./components/FloatChatApp";
import "./globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <FloatChatApp />
  </StrictMode>,
);
