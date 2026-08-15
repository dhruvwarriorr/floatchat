import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { FloatChatApp } from "./components/FloatChatApp";
import "./globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <FloatChatApp />
  </StrictMode>,
);
