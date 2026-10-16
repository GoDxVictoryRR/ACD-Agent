// web/config.js — Frontend configuration
// When deployed separately (e.g. Netlify/Vercel), point API_BASE to the live backend URL.
// When served by FastAPI, empty string means relative to current origin.
const CONFIG = {
  API_BASE: window.location.origin.includes(":3000") || window.location.origin.includes(":3001")
    ? "http://localhost:8000"
    : "",
  POLL_INTERVAL_MS: 300,
};

window.CONFIG = CONFIG;
