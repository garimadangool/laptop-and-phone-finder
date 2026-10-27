# con.md — Project Explained (Laptop Recommendation System for Nepal)

This file explains **every file/folder** in this project: what it does, why it exists,
what tech we used and **where & why** we used it. It also explains what `ui/app.py` is
and what you should do with it.

---

## 1. What is this project?

A **Laptop Recommendation System for Nepali users** (called "LaptopNepal").
The user enters:

- **Budget** (required) — accepts plain numbers (`100000`), Nepali style (`1.5 lakh`) or shorthand (`80k`)
- **Purpose** (required) — gaming, programming, student, video editing, office, AI/ML...
- Optional specs: RAM, storage, storage type, brand, CPU/GPU power tier, screen size, touchscreen

The system scores all 5,284 laptops in the dataset against these inputs and returns a
**ranked top-N list with reasons** ("why this laptop") and penalties ("why not perfect").
If nothing matches exactly, it shows **closest alternatives** instead of an empty page.

---

## 2. Tech stack — what we used, where, and WHY

| Tech | Where | Why we used it |
|---|---|---|
| **Python** | Everything backend | Main language; easy for data + ML work |
| **ML (content-based scoring)** | `model/recommend.py` | We don't train a neural net — we do *feature engineering* (CPU tiers, GPU tiers, purpose labels) then a **weighted scoring algorithm**. This is explainable: every recommendation comes with human-readable "reasons". Perfect for recommendations when you need explanations |
| **pandas / numpy** | available via `requirements.txt`, numpy in charts | Data handling + math (trend lines, correlation heatmap) |
| **scikit-learn** | listed in requirements | Available for future ML models (currently the engine is pure-Python weighted scoring) |
| **FastAPI** | `api/main.py` | The REST **API layer**. Fast, auto-generates `/docs` Swagger UI, uses Pydantic to validate request bodies automatically |
| **Pydantic** | `api/main.py` | Validates that requests have valid budget/purpose/tier ranges before touching the engine |
| **Uvicorn** | runs the API (`run.sh`) | The server that hosts FastAPI on port 8000 |
| **CORS middleware** | `api/main.py` | Lets the React dev server (port 5173) call the API directly without being blocked by the browser |
| **React 19 + Vite** | `frontend/` | The modern e-commerce-style frontend UI. Vite = fast dev server + production bundler |
| **Streamlit** | `ui/app.py` | The **original prototype UI** (quick Python-only UI). Kept as a working legacy demo — see section 4 about `app.py` |
| **Matplotlib** | `visualization/charts.py` | Generates dataset analysis charts as PNGs |
| **pytest** | `tests/` | Automated testing (121 tests passing) |
| **oxlint** | `frontend/` | JavaScript linter for the React code |

**Flow of the app:**

```
User (browser)
   │
   ▼
React frontend  (frontend/, port 5173)
   │  fetch() → /api/recommend  (see src/services/api.js)
   ▼
Vite dev proxy → FastAPI  (api/main.py, port 8000)
   │  calls recommend()
   ▼
Recommendation engine  (model/recommend.py)
   │  loads + scores
   ▼
Dataset  (data/laptops_ml_ready.csv — 5,284 laptops)
```

---

## 3. File-by-file explanation

### Root files

| File | What it is / why it's there |
|---|---|
| `requirements.txt` | All Python dependencies in one place so anyone can install them: `pip install -r requirements.txt`. Includes FastAPI, uvicorn, streamlit, matplotlib, pandas, numpy, scikit-learn, pytest |
| `run.sh` | One-click starter script. Boots **two servers at once**: the FastAPI API on port **8000** and the Streamlit UI on port **8501** (logs go to `/tmp/api.log` and `/tmp/ui.log`). Run it with `bash run.sh`. Note: it currently starts the *Streamlit* UI, not the React one |
| `.pytest_cache/` | Auto-generated cache from running pytest. Safe to ignore/delete |

### Documentation files (the `.md` files)

| File | What it is |
|---|---|
| `instruct.md` | The **original assignment/idea doc** — what the system must do (inputs, ranking, explanations, fallback results). Read this first to understand the goal |
| `21.md` | A **status checklist** of the whole project (dataset ✅, engine ✅, API ✅, UI ✅ ...) plus future phases |
| `LOGBOOK.md` | The full **development diary** — step-by-step log of everything built (Steps 1–12+), decisions made, problems solved |
| `todo.md` | Current **to-do / roadmap** file. Marks what's done (don't redo) and what's left (Phase 5+) |
| `design.md` | Instructions used for the **UI redesign**: make it feel like a modern e-commerce shopping site, not a bank form |
| `g.md` | Follow-up instruction after the redesign attempt: **revert** the disliked redesign direction and improve the *initial* UI instead |
| `con.md` | ← This file |

### `data/`

| File | What it does |
|---|---|
| `laptops_ml_ready.csv` | **The heart of the project.** 5,284 cleaned laptops, one row each. Columns: Brand, CPU/CPU_Brand/CPU_Model, GPU/GPU_Brand/GPU_Model, RAM_GB, Storage_GB, Storage_Type, Screen_Size_Inches, Touchscreen, Operating_System, Weight_KG, Purpose, Price_NPR (prices already converted to Nepali Rupees). This is the result of earlier data collection/cleaning/feature-engineering phases (see LOGBOOK.md) |

### `model/` — the brain (Machine Learning)

| File | What it does |
|---|---|
| `recommend.py` | The entire **recommendation engine**, pure Python. Key pieces:<br>• `CPU_TIERS` / `GPU_TIERS` — hand-built lookup tables mapping hundreds of real CPU/GPU names to power tiers **1–6** (1=budget/integrated, 6=workstation/high-end gaming)<br>• `load_data()` / `preprocess()` — reads the CSV, fills missing values ("Unknown"), converts strings to floats, splits Purpose into labels<br>• `parse_user_budget()` — understands `100000`, `1.5 lakh`, `80k`<br>• `parse_user_purpose()` — maps free text like "video editing and design" to internal labels<br>• `score_laptop()` — **weighted scoring**: budget fit 35%, purpose match 25%, specs 35%, CPU/GPU balance 5% → final 0–100 score with `reasons[]` and `penalties[]`<br>• `recommend()` — filters hard constraints (storage type, screen, touchscreen, dedicated GPU...), scores everything, sorts, returns top N. If zero match → falls back to closest alternatives<br>• `get_dataset_stats()` / `get_available_brands()` — helpers used by both APIs for the stats bar and brand dropdown<br>Run it alone to see demo searches: `python3 model/recommend.py` |
| `__init__.py` | Empty file that makes `model/` a proper Python package so `from model.recommend import ...` works |

### `api/` — the backend API

| File | What it does |
|---|---|
| `main.py` | **FastAPI application** — the middleman between any frontend and the engine.<br>Endpoints:<br>• `GET /` — info + endpoint list<br>• `POST /recommend` — main endpoint: takes JSON (budget, purpose, optional filters) → returns ranked recommendations with score/reasons/penalties<br>• `GET /brands` — list of brands (for dropdowns)<br>• `GET /purposes` — valid purpose labels<br>• `GET /stats` — dataset stats (total laptops, brands count, price range) shown in the hero section<br>CORS is configured so localhost:5173/4173/3000/8501 frontends can call it. Pydantic models (`RecommendRequest`, `LaptopOut`, ...) validate and document everything automatically.<br>Interactive docs auto-generated at **http://localhost:8000/docs** |
| `__init__.py` | Makes `api/` a package |

### `frontend/` — the modern React UI

Built with **React 19 + Vite**. Looks like a real e-commerce shopping site.

| File | What it does |
|---|---|
| `package.json` | Node project config. Scripts: `npm run dev` (dev server :5173), `npm run build` (production build → `dist/`), `npm run lint` (oxlint). Deps: react, react-dom |
| `vite.config.js` | Vite setup + **dev proxy**: any `/api/*` request from React is forwarded to `http://localhost:8000` (strips `/api` prefix). That's why no CORS pain during development |
| `index.html` | Single HTML shell that React mounts into |
| `public/favicon.svg` | Browser tab icon |
| `src/main.jsx` | Entry point — mounts `<App />` into the page |
| `src/App.jsx` | Top-level state manager: holds search results, compare tray items (up to 4 laptops), detail modal, and fetches `/stats` for hero counters |
| `src/services/api.js` | Thin **fetch wrapper** around the FastAPI backend: `getRecommendations()`, `getBrands()`, `getPurposes()`, `getStats()`. Handles errors nicely (parses FastAPI validation errors). Uses `VITE_API_BASE_URL` env var if set, else `/api` |
| `src/data/options.js` | All static option data (purposes with emojis/blurb, budget presets, RAM/storage options). Purpose labels here MUST stay in sync with `ALL_PURPOSE_LABELS` in `model/recommend.py` |
| `src/styles/index.css` | Global styles/design tokens (colors, fonts, layout) |
| `src/components/Navbar.jsx/.css` | Top navigation bar |
| `src/components/Hero.jsx/.css` | Big welcome banner with live dataset counters |
| `src/components/FinderSection.jsx/.css` | The search form: purpose grid + budget slider + optional preferences |
| `src/components/PurposeGrid.jsx/.css` | Clickable purpose cards (Gaming 🎮, Student 📚 ...) |
| `src/components/BudgetSelector.jsx/.css` | Budget slider + preset chips (Under 50K, 1 Lakh...) |
| `src/components/PreferencesPanel.jsx/.css` | Optional advanced filters (RAM, storage, brand, tiers...) |
| `src/components/ResultsSection.jsx/.css` | Renders the ranked result cards with score badges, price, reasons |
| `src/components/LaptopDetail.jsx/.css` | Detail modal when you click a laptop |
| `src/components/CompareTray.jsx/.css` | Bottom bar showing picked laptops to compare (up to 4) |
| `src/components/CompareModal.jsx/.css` | Side-by-side spec comparison table |
| `src/components/Footer.jsx/.css` | Page footer |
| `dist/` | Prebuilt production output of `npm run build` (static files ready to host) |

### `ui/` — the OLD Streamlit interface (legacy)

| File | What it does |
|---|---|
| `app.py` | **Streamlit prototype** — the original quick UI built before the React frontend existed. Pure Python: renders hero, stats bar, 3-step flow (purpose → budget → optional specs), and pretty HTML/CSS laptop cards with SVG drawings, score labels (Excellent/Great/Good...), NPR prices. Still fully working |
| `static/style.css` | Custom CSS injected into Streamlit to make it look like a product site instead of default Streamlit gray boxes |

### `visualization/` — data analysis charts

| File/Folder | What it does |
|---|---|
| `charts.py` | Script that generates **8 analysis charts** from the dataset using Matplotlib (dark themed): price distribution histogram, brand market share, price-by-brand boxplot, purpose distribution, RAM vs price scatter + trend line, CPU/GPU tier distributions, correlation heatmap, storage type vs price. Run: `python3 visualization/charts.py` |
| `charts/*.png` | The generated chart images (01–08) — useful for reports/presentations |

### `tests/` — automated tests

| File | What it tests |
|---|---|
| `test_recommend.py` | Unit tests for the engine: budget parsing (`lakh`/`k`), purpose mapping, tier lookups, scoring weights, fallback behavior, performance |
| `test_api.py` | API tests using FastAPI's TestClient: every endpoint returns correct status codes and JSON shapes, validation errors handled |
| `test_e2e.py` | End-to-end pipeline tests: simulated user input → API → recommendations, verifying the whole chain works together |
| `__init__.py` | Makes it a package |

Run all tests: `python3 -m pytest tests/ -v` (121 tests, all passing).

---

## 4. About `ui/app.py` — what is it and what to do with it?

**What it is:** the *original* Streamlit user interface — a fast prototype built while the
backend was being developed, before the React frontend was created. It talks **directly**
to `model/recommend.py` (no HTTP involved).

```
ui/app.py ──imports──▶ model/recommend.py ──reads──▶ data/laptops_ml_ready.csv
```

**Do you still need it?** No — the React frontend (`frontend/`) is the real UI now.
But it's kept because:
1. It still works as a quick demo (no npm/node needed — just Python).
2. It proves the engine works end-to-end.
3. It's part of project history (LOGBOOK steps).

**Your three options with `app.py`:**

| Option | How |
|---|---|
| Keep it as a backup/demo | Do nothing — it costs nothing |
| Run it | `streamlit run ui/app.py --server.port 8501` or just `bash run.sh` |
| Delete it | Remove `ui/` folder entirely, remove `streamlit>=1.22.0` from `requirements.txt`, and update `run.sh` (it currently launches Streamlit!) — the React app doesn't depend on it at all |

⚠️ Note: `bash run.sh` currently starts **Streamlit**, not React. To use the modern UI,
run two terminals:

```bash
# Terminal 1 — API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — React frontend
cd frontend && npm run dev     # open http://localhost:5173
```

---

## 5. Quick command cheat-sheet

```bash
pip install -r requirements.txt        # install Python deps
python3 model/recommend.py             # test the engine in terminal (demo searches)
python3 -m pytest tests/ -v            # run all 121 tests
uvicorn api.main:app --port 8000       # start API → http://localhost:8000/docs
cd frontend && npm install             # first time only
cd frontend && npm run dev             # start React UI → http://localhost:5173
cd frontend && npm run build           # production build → dist/
streamlit run ui/app.py                # legacy Streamlit UI → :8501
python3 visualization/charts.py        # regenerate analysis PNGs
```
