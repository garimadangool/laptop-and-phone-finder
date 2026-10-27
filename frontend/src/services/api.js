// Thin fetch wrapper around the existing FastAPI backend.
// In development Vite proxies /api -> http://localhost:8000 (see vite.config.js).
// For a deployed frontend set VITE_API_BASE_URL to the API origin.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error(
      "Cannot reach the recommendation server. Is the FastAPI backend running on port 8000?"
    );
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (Array.isArray(body.detail) && body.detail.length > 0) {
        detail = body.detail.map((d) => d.msg).join(", ");
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      /* keep default message */
    }
    throw new Error(detail);
  }
  return res.json();
}

export function getRecommendations(payload) {
  return request("/recommend", { method: "POST", body: JSON.stringify(payload) });
}

export function getBrands() {
  return request("/brands");
}

export function getPurposes() {
  return request("/purposes");
}

export function getStats() {
  return request("/stats");
}

export function getInsights() {
  return request("/insights");
}

// ---------- Phone endpoints ----------

export function getPhoneRecommendations(payload) {
  return request("/phones/recommend", { method: "POST", body: JSON.stringify(payload) });
}

export function getPhoneBrands() {
  return request("/phones/brands");
}

export function getPhonePurposes() {
  return request("/phones/purposes");
}

export function getPhoneStats() {
  return request("/phones/stats");
}

export function getPhoneInsights() {
  return request("/phones/insights");
}

export function askPhoneAI({ question, history = [], top_n = 5, max_price = null, brand = null, laptop = null }) {
  return request("/phones/ask-ai", {
    method: "POST",
    body: JSON.stringify({ question, history, top_n, max_price, brand, laptop }),
  });
}

export async function streamPhoneAskAI(payload, onEvent, signal) {
  let res;
  try {
    res = await fetch(`${API_BASE}/phones/ask-ai/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch {
    throw new Error("Cannot reach the recommendation server. Is the FastAPI backend running on port 8000?");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch { /* keep */ }
    throw new Error(detail);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalEvent = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event = JSON.parse(line);
        onEvent(event);
        if (event.type === "done" || event.type === "error") finalEvent = event;
      } catch { /* ignore */ }
    }
  }
  return finalEvent;
}

// ---------- Ask AI chatbot (grounded by RAG, answered by a local LLM) ----------

// Non-streaming fallback: one JSON payload with the full answer + cited sources.
export function askAI({ question, history = [], top_n = 5, max_price = null, brand = null, laptop = null }) {
  return request("/ask-ai", {
    method: "POST",
    body: JSON.stringify({ question, history, top_n, max_price, brand, laptop }),
  });
}

// Streaming variant: reads newline-delimited JSON events from POST /ask-ai/stream.
// Calls onEvent({type, ...}) per event; returns the final "done" event (or null
// when the stream ended without one / failed mid-way).
export async function streamAskAI(payload, onEvent, signal) {
  let res;
  try {
    res = await fetch(`${API_BASE}/ask-ai/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch {
    throw new Error(
      "Cannot reach the recommendation server. Is the FastAPI backend running on port 8000?"
    );
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep default message */
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalEvent = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep the trailing partial line in the buffer
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event = JSON.parse(line);
        onEvent(event);
        if (event.type === "done" || event.type === "error") finalEvent = event;
      } catch {
        /* ignore malformed line */
      }
    }
  }
  return finalEvent;
}

// ---------- Interaction logging (fire-and-forget, never breaks UX) ----------

// One id per search; click events reference it so future ML can link
// "what was shown" with "what the user actually opened".
let currentSid = null;

export function beginSearch() {
  currentSid =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `sid-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return currentSid;
}

function post(path, body) {
  return request(path, { method: "POST", body: JSON.stringify(body) }).catch(
    () => null
  );
}

export function logSearch(payload, data) {
  const recs = data?.recommendations ?? [];
  return post("/log-search", {
    ...payload,
    client_sid: currentSid,
    status: data?.status ?? "",
    results_shown: recs.length,
    top_score: recs[0]?.score ?? null,
  });
}

export function logClick(action, rec, extra = {}) {
  const base = { action, client_sid: currentSid, ...extra };
  if (!rec) return post("/log-click", base);
  const { laptop, score } = rec;
  return post("/log-click", {
    ...base,
    position: typeof rec._rank === "number" ? rec._rank - 1 : null,
    score: score ?? null,
    brand: laptop.brand,
    cpu_model: laptop.cpu_model,
    gpu_model: laptop.gpu_model,
    ram_gb: laptop.ram_gb,
    storage_gb: laptop.storage_gb,
    storage_type: laptop.storage_type || null,
    price_npr: laptop.price_npr,
    os: laptop.os || null,
    screen_size: laptop.screen_size || null,
  });
}
