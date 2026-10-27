# TODO — LaptopFinder Nepal (AI Laptop Recommendation System)

> Pick up where you left off. Everything below Phase 5 of 21.md is future work.
> Logbook has full details of what's done: see `LOGBOOK.md` → Steps 1–13.

---

## ✅ DONE (don't redo)

- [x] Dataset collection, cleaning, feature engineering → `data/laptops_ml_ready.csv` (5,284 rows)
- [x] Recommendation engine (content-based scoring) → `model/recommend.py`
- [x] FastAPI backend with all endpoints → `api/main.py` (+ CORS added for frontend)
- [x] Dataset visualization charts → `visualization/charts/`
- [x] Streamlit prototype → `ui/app.py` (kept as legacy, still works)
- [x] Test suite: 121 tests passing → `tests/`
- [x] **React frontend Phases 1–3** — homepage, finder flow (multi-purpose select!), live recommendations
- [x] **Phase 4** — product details modal (View Details works)
- [x] **Phase 5** — comparison view (Compare tray + side-by-side table with best-value ★)
- [x] **UI Polish & QA (Step 1)** — multi-purpose combo QA ✓, per-brand laptop images (`LaptopVisual.jsx`) ✓, loading skeletons ✓ — LOGBOOK Step 13
- [x] **Market Insights on the website (Step 14)** — `GET /insights` endpoint + Recharts section (price histogram, top brands, purpose split, RAM-vs-price, CPU/GPU tiers, storage donut); 135 tests passing — LOGBOOK Step 14
- [x] **Click logging (Step 15)** — SQLite `data/interactions.db` via `api/interactions.py`; `POST /log-search` + `POST /log-click` + `GET /logs/stats`; frontend logs every search (params + results + ranks) and click (view_details / compare_add+remove / show_more) fire-and-forget; 143 tests passing; inspect via `/logs/stats` or `api.interactions.export_json()` — LOGBOOK Step 15
- [x] **RAG retrieval (Step 16)** — ChromaDB vector index of all 5,284 laptops at `data/chroma/` built by `model/rag.py` (`python3 -m model.rag`); `GET /ask?query=...` returns grounded laptops straight from the dataset (+ auto-parses budget phrases like "under 80k", optional `max_price`/`brand` filters); 172 tests passing — LOGBOOK Step 16
- [x] **LLM "Ask AI" chatbot (Step 17)** — local Ollama + Mistral on the Windows host (`OLLAMA_HOST=0.0.0.0` set; WSL auto-detects gateway IP); `model/llm.py` builds grounded prompts; `POST /ask-ai` + `/ask-ai/stream` (NDJSON) in FastAPI; 🤖 Ask AI button in LaptopDetail now opens a real streaming chat panel with suggestion chips, typing indicator and "grounded on N dataset laptops" chips; 206 tests passing — LOGBOOK Step 17

## ▶️ HOW TO RUN

```bash
# Terminal 1 — API (required)
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — React frontend
cd ~/garima/frontend && npm run dev    # → http://localhost:5173
```

Note: Node.js is installed at `~/.local/lib/node` (symlinks in `~/.local/bin`).

---

## 🔜 NEXT UP (in order)

### 1. Polish & QA the React UI
- [ ] Test the full flow manually on desktop + mobile widths (resize browser) — in progress: compare-table scroll fixed 3 ways (table min-width, flex `min-width:0`, mouse drag-to-scroll + visible scrollbar — LOGBOOK 13.6); hard-refresh browser before retesting; "Show more" reveal added (13.7); Ask AI chat panel added (Step 17) — test it too; keep checking
- [x] Check multi-purpose combos give sensible results (e.g. Gaming + Programming) — verified via engine + live API
- [x] Add laptop images per brand → `frontend/src/components/LaptopVisual.jsx` (26 brand themes, classic/gaming/ultra variants)
- [x] Loading skeletons for result cards while fetching (`SkeletonCard`, shimmer, reduced-motion safe)

### 2. Click logging ✅ DONE (LOGBOOK Step 15) — collect interactions before touching ML
- [x] SQLite `data/interactions.db`: `search_events` + `click_events` tables (timestamp, params, results shown, which card was opened)
- [x] `POST /log-search` + `POST /log-click` + `GET /logs/stats` in FastAPI (`api/interactions.py`)
- [ ] Later: use this data for collaborative filtering / learning-to-rank — need a few hundred real interactions first

### 3. RAG ✅ DONE (LOGBOOK Step 16) — retrieval is grounded in the dataset
- [x] Install ChromaDB (free, local): `pip install chromadb` → added to requirements.txt
- [x] Index each laptop's specs into a vector collection → `data/chroma/` via `model/rag.py`; every laptop becomes a natural-language spec-sheet doc + its full formatted record as metadata (5,284 docs, cosine space)
- [x] Retrieval endpoint: GET /ask?query=... returns relevant laptops from your dataset — auto-extracts budget phrases ("under 80k", "below 1 lakh"), optional `max_price`/`brand`/`top_n` params
- [x] Keeps answers grounded in YOUR data — answers are indexed dataset rows only, retrieval is local + deterministic + fast (~11ms/query); embeddings are TF-IDF vectors stored directly in Chroma (no model downloads; swap-in point for MiniLM/BGE noted for the LLM step)
- Note: rebuild after dataset changes → `python3 -m model.rag`

### 4. LLM "Ask AI" chatbot ✅ DONE (LOGBOOK Step 17)
- [x] Wire the existing disabled 🤖 Ask AI button (LaptopDetail.jsx footer) → opens `AskAiPanel` streaming chat
- [x] Free tier → **local Ollama + Mistral** (user's machine, Windows side; no key needed at all — better than Groq/Gemini sketch)
- [x] Pipeline: user question → retrieve laptops via RAG → LLM answers citing them (`POST /ask-ai`, `/ask-ai/stream`)
- [x] Keep recommend.py as the source of truth; LLM only explains (system prompt locked to retrieved documents; sources echoed in response)
- [x] Never expose the API key in frontend — proxy through FastAPI (moot: fully local, zero keys; all prompting server-side)
- Note: needs Ollama running on Windows with `OLLAMA_HOST=0.0.0.0` (already set persistently via setx); restart uvicorn :8000 if it predates this change

### 5. Deployment
- [ ] Frontend: Vercel or Netlify (`npm run build`, deploy `frontend/dist`)
- [ ] Backend: Render / Railway free tier
- [ ] Set `VITE_API_BASE_URL` env var in frontend to the deployed API URL
- [ ] Lock CORS origins in api/main.py to your real domain

### 6. Nice-to-haves (later)
- [ ] Price history tracking (scrape periodically)
- [ ] Dark mode toggle
- [ ] User accounts / saved shortlists
- [ ] Nepali language toggle (i18n)
- [ ] README.md with screenshots + setup instructions

---

## ⚠️ REMINDERS

- Do NOT rewrite `model/recommend.py`, the dataset, or backend logic without need
- Purpose labels in `frontend/src/data/options.js` MUST stay in sync with `ALL_PURPOSE_LABELS` in recommend.py
- Compare max = 4 laptops; compare clears automatically on new search
- `/ask` needs the ChromaDB index at `data/chroma/` — if the dataset changes, rebuild with `python3 -m model.rag` (API returns 503 with this hint when missing)
- Ask AI needs Ollama running on Windows (`OLLAMA_HOST=0.0.0.0` already set via setx; mistral pulled). If unreachable, /ask-ai returns 503 listing probed hosts; `OLLAMA_BASE_URL`/`OLLAMA_MODEL` env vars override defaults
