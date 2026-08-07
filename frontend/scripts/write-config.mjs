import { writeFileSync } from "node:fs";

const apiBaseUrl = process.env.VITE_API_BASE_URL || process.env.GEMINI_API_BASE_URL || "";

writeFileSync(
  new URL("../config.js", import.meta.url),
  `window.GEMINI_API_BASE_URL = ${JSON.stringify(apiBaseUrl)};\n`,
);
