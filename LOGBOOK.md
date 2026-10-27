# Laptop Recommendation System - Development Logbook

## Project Overview
Building a laptop recommendation system that takes user requirements (budget, purpose, specifications) and returns ranked laptop recommendations with explanations.

**Required Technologies:** Python, Machine Learning, API, Data Visualization

---

## Step 1: Project Understanding & Data Exploration

**Status:** Completed

### Requirements (from instruct.md)
- User inputs: Budget (required), Purpose (required), RAM, Storage, CPU, GPU, Brand, other specs (all optional)
- System must rank and recommend laptops matching user needs
- Show recommended laptops with specs and price
- Provide explanation for each recommendation
- Handle no-exact-match by showing closest alternatives
- Simple user interface for input/output

### Dataset Analysis
- **File:** `data/laptops_ml_ready.csv`
- **Records:** 5,319 laptops (excluding header)
- **Columns:** 19 columns
  - `Brand` - Laptop manufacturer
  - `CPU` - Full CPU string
  - `CPU_Brand` - Intel/AMD
  - `CPU_Model` - CPU model name
  - `GPU` - Full GPU string
  - `GPU_Brand` - Intel/NVIDIA/AMD
  - `GPU_Model` - GPU model name
  - `RAM_GB` - RAM in GB
  - `Storage_GB` - Storage size (has missing values)
  - `Storage_Type` - SSD/HDD/Flash Storage
  - `Screen_Size_Inches` - Display size
  - `Touchscreen` - 0.0/1.0 boolean
  - `IPS_Panel` - 0.0/1.0 boolean
  - `Operating_System` - OS name
  - `Weight_KG` - Weight in kg
  - `Warranty` - Warranty info (all missing)
  - `Price` - Base price
  - `Purpose` - Use case (General Use, Student, Gaming, Office)
  - `Price_NPR` - Price in Nepali Rupees

### Data Quality Notes
- `Storage_GB` has missing values - needs imputation
- `Warranty` column is entirely empty - can be dropped
- `CPU` and `GPU` columns appear empty (redundant with `CPU_Model`/`GPU_Model`)
- `Price` and `Price_NPR` are identical - keep one
- Categorical columns need encoding for ML

---

## Step 2: Data Preprocessing & Feature Engineering

**Status:** Completed

### Completed Tasks (Offline CSV)
- [x] Dropped columns with >=50% missing: `IPS_Panel` (59.8%), `Warranty` (64.1%)
- [x] Dropped duplicate column: `Price` (identical to `Price_NPR`)
- [x] Removed 35 exact duplicate rows
- [x] Saved cleaned CSV: 5,284 rows, 16 columns

### Completed Tasks (Runtime in `model/recommend.py`)
Missing values were handled at runtime in the recommendation engine rather than imputing the CSV. This keeps the raw data intact while providing sensible defaults during scoring:
- [x] `Storage_GB` (40.3% missing) → defaults to `0.0`
- [x] `Storage_Type` (43.0% missing) → defaults to `"Unknown"`
- [x] `Touchscreen` (43.0% missing) → defaults to `0.0`
- [x] `Weight_KG` (35.9% missing) → defaults to `0.0`
- [x] `Screen_Size_Inches` (19.0% missing) → defaults to `0.0`
- [x] `Operating_System` (18.9% missing) → defaults to `"Unknown"`
- [x] `CPU` (10.9% missing) → defaults to `"Unknown"`
- [x] `GPU` (11.0% missing) → defaults to `"Integrated"`
- [x] `Brand` (0.4% missing) → defaults to `"Unknown"`
- [x] Parse `Purpose` column at runtime via keyword matching to 10 canonical labels
- [x] CPU tier/grade feature (1-6 scale) created via keyword matching at runtime
- [x] GPU tier/grade feature (1-6 scale) created via keyword matching at runtime
- [x] Numerical features compared directly in scoring (normalization not needed for rank-based approach)

---

## Step 3: ML Model Development (Recommendation Engine)

**Status:** Completed

### Approach: Content-Based Scoring & Ranking
No user interaction data available, so content-based filtering was chosen.

### Implementation (`model/recommend.py`)
- **Preprocessing:** Fills missing values with sensible defaults (Unknown/0)
- **CPU Tier Scoring (1-6):** Based on model family mapping (Celeron/Pentium=1, i3/Ryzen3=2, i5/Ryzen5 gen7=3, i7/Ryzen7 gen7=4, i9/Ryzen9=5, Threadripper/M-series=6)
- **GPU Tier Scoring (1-6):** Based on model family mapping (Radeon R2-5/HD400=1, HD620/UHD620/MX=2, GTX1050/RTX3050/IrisXe=3, GTX1060/RTX4050=4, RTX3060-3080/RTX4060-4070=5, RTX4090/RTX5080-5090=6)
- **Purpose Parsing:** Free-text input mapped to 10 canonical labels via keyword matching
- **Scoring Weights:** Budget (35%) + Purpose (25%) + Specs (35%) + Balance (5%)
- **Explanation Generation:** Per-recommendation reasons and penalties
- **Edge Cases:** Falls back to closest alternatives if no exact match; filters out >150% budget over

### Test Results
All 6 test queries returned valid results:
1. Gaming/100K budget: Infinix RTX 4060 (94,990 NPR) - top score 97.79
2. Programming/80K: MSI RTX 5070 (79,999 NPR) - top score 93.42
3. Student/50K: Acer RTX 4050 (39,999 NPR) - top score 77.29
4. Video Editing/200K: MSI RTX 4090 (179,888 NPR) - top score 100
5. Office/30K: Lenovo RTX 3050 (29,999 NPR) - top score 75.54
6. ML-AI/150K/Dell: Dell RTX 5070 (112,000 NPR) - top score 93.18

---

## Step 4: API Development

**Status:** Completed

### Implementation (`api/main.py`)
- **Framework:** FastAPI with Pydantic request validation
- **Run:** `python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000`

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info and endpoint list |
| POST | `/recommend` | Get ranked laptop recommendations |
| GET | `/brands` | List all 27 available brands |
| GET | `/purposes` | List 10 purpose labels |
| GET | `/stats` | Dataset statistics (5284 laptops) |
| GET | `/docs` | Interactive Swagger documentation |

### Test Results
All endpoints tested successfully:
- `/` - Returns API info
- `/brands` - Returns 27 brands (HP, Lenovo, ASUS, Dell, MSI...)
- `/purposes` - Returns 10 labels (AI/ML, Gaming, Programming, etc.)
- `/stats` - Returns totals, brand distribution, price range (6,499 - 1,130,809 NPR)
- `/recommend` (gaming 100K) - Found 2582 matches, top: Infinix RTX 4060 94,990 NPR
- `/recommend` (programming 60K) - Top: Apple M1 54,490 NPR
- `/recommend` (gaming 10K low budget) - Found 82 matches, top: Infinix i3 8,499 NPR

---

## Step 5: Data Visualization

**Status:** Completed

### Implementation (`visualization/charts.py`)
- **Libraries:** matplotlib, seaborn
- **Theme:** Dark mode with custom color scheme
- **Run:** `python3 visualization/charts.py`

### Generated Charts (`visualization/charts/`)
| # | Chart | Description |
|---|-------|-------------|
| 1 | `01_price_distribution.png` | Histogram of laptop prices with median line |
| 2 | `02_brand_market_share.png` | Top 12 brands by laptop count (horizontal bar) |
| 3 | `03_price_by_brand.png` | Box plot of price ranges per brand |
| 4 | `04_purpose_distribution.png` | Laptops per purpose label (horizontal bar) |
| 5 | `05_ram_vs_price.png` | Scatter plot with trend line |
| 6 | `06_cpu_gpu_tiers.png` | Side-by-side bar charts of CPU/GPU tier distribution |
| 7 | `07_correlation_heatmap.png` | Correlation matrix of numerical features |
| 8 | `08_storage_vs_price.png` | Storage vs Price colored by type (SSD/HDD/Flash) |

---

## Step 6: User Interface

**Status:** Completed

### Implementation
- **Framework:** Streamlit + external CSS
- **Files:**
  - `ui/app.py` — Streamlit application
  - `ui/static/style.css` — External stylesheet (clean, minimal design)
- **Run:** `streamlit run ui/app.py`

### Features
- **Sidebar inputs:** Budget (free text with flexible parsing), Purpose dropdown, optional specs
- **Optional fields:** RAM, Storage, Storage Type, Brand, Screen Size, Touchscreen
- **Recommendation cards:** Rank, score badge, laptop specs grid, reason/penalty tags
- **Empty state:** Welcome message with dataset stats
- **Responsive:** Centered layout, max-width 900px

### Design
- **Color scheme:** White background, #0984e3 blue accent, #2d3436 dark text
- **CSS file:** Separated into `ui/static/style.css` (200+ lines)
- **Score badges:** Gradient blue-purple with label (Excellent/Great/Good/Fair)
- **Reason tags:** Green for positives, orange for penalties
- **Hover effects:** Cards lift on hover with blue border highlight

---

## Step 7: Testing & Integration

**Status:** Completed

### Implementation (`tests/`)
- **Framework:** pytest
- **Run:** `python3 -m pytest tests/ -v`

### Test Files
| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_recommend.py` | 91 tests | Unit tests for all model functions |
| `tests/test_api.py` | 19 tests | API endpoint integration tests |
| `tests/test_e2e.py` | 10 tests | End-to-end pipeline tests |

### Test Results
All tests pass: 121 passed (91 unit + 19 API + 10 E2E = 120 total + 1 performance = 121).

#### Unit Tests (`tests/test_recommend.py`)
| Category | Tests | Status |
|----------|-------|--------|
| Data Loading & Preprocessing | 8 | All pass |
| CPU Tier Scoring | 15 | All pass |
| GPU Tier Scoring | 13 | All pass |
| Budget Parsing | 9 | All pass |
| Purpose Parsing | 15 | All pass |
| Scoring Logic | 9 | All pass |
| Recommend Function | 11 | All pass |
| Dataset Stats | 4 | All pass |
| Available Brands | 3 | All pass |
| Performance | 2 | All pass (<2s per query) |

#### API Tests (`tests/test_api.py`)
| Endpoint | Tests | Status |
|----------|-------|--------|
| GET `/` | 1 | Pass |
| GET `/brands` | 2 | Pass |
| GET `/purposes` | 2 | Pass |
| GET `/stats` | 2 | Pass |
| POST `/recommend` | 12 | Pass (including edge cases) |

#### E2E Tests (`tests/test_e2e.py`)
| Scenario | Status |
|----------|--------|
| UI input -> API response pipeline | Pass |
| API matches direct model call | Pass |
| All purpose variations via API | Pass |
| Budget format variations via API | Pass |
| Fallback when no exact match | Pass |
| Dataset stats consistency | Pass |
| Brand consistency across endpoints | Pass |
| Gaming budget end-to-end | Pass |
| Student low budget end-to-end | Pass |
| Brand filter end-to-end | Pass |

### Bugs Fixed During Testing
- Fixed `budget` `None` crash when empty string passed (model/recommend.py:467-468)
- Fixed preprocess default values to use `0.0` (float) instead of `0` (int) for numeric fields
- Added missing GPU tier pattern `"geforce rtx 3050"` (without trailing space) to tier 3

---

## Step 8: Testing, QA & Finalization

**Date:** 2026-08-20
**Status:** Completed

### What Was Done
This session focused on completing all remaining project tasks: writing a comprehensive test suite, fixing bugs discovered during testing, adding UI error handling, creating a `requirements.txt`, and updating the logbook.

### 8.1 Created `requirements.txt`
- Added all project dependencies with minimum version constraints
- Includes: pandas, numpy, scikit-learn, fastapi, uvicorn, matplotlib, seaborn, streamlit, httpx, pytest

### 8.2 Wrote Comprehensive Test Suite (121 tests total)
- **Unit tests** (`tests/test_recommend.py`) — 91 tests covering:
  - Data loading & preprocessing (8 tests)
  - CPU tier scoring with 15 real CPU models (15 tests)
  - GPU tier scoring with 13 real GPU models (13 tests)
  - Budget parsing with formats like lakh, lac, k, commas (9 tests)
  - Purpose parsing with 15 keyword variations (15 tests)
  - Scoring logic: budget, purpose, brand, RAM matching (9 tests)
  - Recommend function with various inputs (11 tests)
  - Dataset stats & brands (7 tests)
  - Performance benchmarks (<2s per query) (2 tests)

- **API integration tests** (`tests/test_api.py`) — 19 tests covering:
  - All 5 endpoints (root, brands, purposes, stats, recommend)
  - Missing required fields (422 errors)
  - Edge cases: empty body, negative top_n, low/high budgets
  - Response structure validation

- **End-to-end tests** (`tests/test_e2e.py`) — 10 tests covering:
  - Full UI input → API → Model → Response pipeline
  - API matches direct model call
  - All purpose variations (9 labels) via API
  - Budget format variations (8 formats) via API
  - Fallback when no exact match found
  - Dataset stats consistency across endpoints
  - Brand filter end-to-end

### 8.3 Bugs Found & Fixed
| Bug | Location | Fix |
|-----|----------|-----|
| `budget` `None` crash when empty string passed | `model/recommend.py:467-468` | Explicit `None` check: `budget = _budget if _budget is not None else 0` |
| Preprocess defaults were `0` (int) not `0.0` (float) | `model/recommend.py:246` | Changed defaults to `0.0` for all numeric fields |
| RTX 3050 not matched by GPU tier (pattern had trailing space) | `model/recommend.py:186` | Added `"geforce rtx 3050"` (without trailing space) to tier 3 patterns |

### 8.4 UI Error Handling (`ui/app.py`)
- Added `try/except` around recommendation call to catch unexpected errors
- Added validation for negative RAM/storage values
- Added validation for zero/negative budget
- User sees friendly error message instead of app crash

### 8.5 Updated Logbook
- Updated Step 2 status from "Partially Completed" to "Completed"
- Documented runtime preprocessing approach for missing values
- Added this section (Step 8) documenting the full session
- Updated project file structure to include `tests/`, `requirements.txt`

---

## Step 9: UI Redesign (design.md)

**Date:** 2026-08-20
**Status:** Completed

### What Was Done
Complete frontend redesign following design.md requirements. Moved from a sidebar-heavy layout to a guided, card-based shopping assistant experience.

### 9.1 New UX Flow
- **Hero section** — Welcome banner with laptop icon and stats
- **Step 1: Purpose** — Visual purpose cards (Gaming, Programming, Student, Creative Work, Office, Everyday Use) with icons and hover/selected states
- **Step 2: Budget** — Text input with quick-pick budget chips (30K, 50K, 80K, 1 Lakh, 1.5 Lakh, 2 Lakh+)
- **Step 3: Specs** — Expandable optional specs section (RAM, Storage, Brand, Screen, Touchscreen, Dedicated GPU, CPU/GPU tiers)
- **Find button** — Centered CTA to trigger recommendations
- **Results** — Product-style recommendation cards with rank badges, score pills, spec pills, reason/penalty tags

### 9.2 Visual Redesign
- **Theme:** Light only, soft off-white (#f5f3f0) background, dark charcoal (#2c2c2c) text
- **Accent:** Muted teal (#5b8a8a) — accessible, calming, distinctive
- **Typography:** Inter font family, modern and readable
- **Cards:** Rounded corners (12-16px), subtle shadows, hover lift effects
- **Spec display:** Pill-style tags (label + value) instead of grid cells
- **Rank badges:** Square badges with top-pick crown indicator
- **Score pills:** Teal background with dot indicator
- **Reason/penalty tags:** Green (#5a9a6a) for positives, orange (#c47a3a) for warnings

### 9.3 Accessibility
- WCAG-compliant contrast ratios throughout
- Information not conveyed by color alone (icons, labels, text, shape)
- Readable font sizes (min 0.75rem)
- Clear selected/unselected states via borders + background + text
- Logical layout structure

### 9.4 Responsive Design
- 3-column purpose cards on desktop, 2-column on mobile
- 4-column stats grid, 2-column on smaller screens
- Card layout adapts to screen width

### 9.5 Files Modified
- `ui/app.py` — Complete rewrite (guided step flow, card-based rendering, session state)
- `ui/static/style.css` — Complete rewrite (design system, CSS variables, responsive)

---

## Step 10: Optional Specs & OS/Dedicated GPU Filters

**Date:** 2026-08-20
**Status:** Completed

### What Was Done
Added optional spec filters to the recommendation system and improved the spec display to show known values instead of "N/A".

### 10.1 New Optional Filters
| Filter | Type | Description |
|--------|------|-------------|
| OS Preference | Selectbox | Filter by Windows, macOS, Linux, Chrome OS |
| CPU Tier | Slider (0-6) | Minimum processor power level |
| GPU Tier | Slider (0-6) | Minimum graphics power level |
| Dedicated GPU | Checkbox | Exclude integrated graphics |

### 10.2 OS Filtering Fix
- **Problem:** "Unknown" OS laptops (1,001 of 5,284) were passing through the OS filter, showing Windows laptops when macOS/Linux was selected
- **Fix:** When a specific OS is chosen, laptops with "Unknown" or "No OS" are now excluded
- **Result:** macOS → Apple only (32 laptops), Linux → Linux only (73 laptops)

### 10.3 Dedicated GPU Filter
- Added checkbox to filter out Intel/Integrated GPUs
- Only shows laptops with NVIDIA, AMD, or other dedicated GPU brands
- Useful for gaming, video editing, ML workloads

### 10.4 Smart Spec Display
- Instead of showing "N/A" for unknown weight/screen/storage, dynamically builds a list of 8 possible specs
- Shows up to 6 known specs, skipping unknown values
- Available spec slots: RAM, Storage, GPU, CPU, OS, Screen, Weight, Touchscreen

### 10.5 Files Modified
- `model/recommend.py` — Added OS/dedicated_gpu filtering and scoring logic
- `api/main.py` — Added `os` and `dedicated_gpu` fields to request model
- `ui/app.py` — Added OS, CPU tier, GPU tier, dedicated GPU to sidebar

---

## Step 11: UI Redesign — E-Commerce Shopping Theme

**Date:** 2026-08-20
**Status:** Completed

### What Was Done
Complete UI redesign following g.md requirements. Reverted away from the washed-out design.md direction and rebuilt the UI as a polished e-commerce laptop shopping platform with strong colour contrast and visual depth.

### 11.1 Design Direction
- **Theme:** Modern e-commerce laptop shopping website
- **Primary:** Royal blue (#2563eb) — strong, trustworthy
- **Secondary:** Violet (#7c3aed) — accent, badges, gradients
- **Success:** Emerald (#059669) — prices, scores, positive tags
- **Background:** Cool light grey (#f1f5f9)
- **Text:** Near-black (#0f172a) for strong contrast
- **Light theme only** — no dark mode

### 11.2 Layout
- **Hero section:** Deep blue-to-violet gradient with laptop SVG illustration, tagline, and description
- **Stats bar:** 4-column grid showing dataset stats (5,284 laptops, 27 brands, etc.)
- **Step 1:** Purpose category cards with icons (Gaming, Programming, Student, Creative Work, Office, Everyday)
- **Step 2:** Budget input with quick-pick chips (30K → 2 Lakh+)
- **Step 3:** Expandable optional specs
- **Results:** Horizontal product cards with brand-coloured laptop SVG images

### 11.3 Product Cards (E-Commerce Style)
- Horizontal layout: image left, details right
- Brand-coloured laptop SVG illustrations (HP blue, Lenovo red, ASUS navy, Dell blue, MSI red, etc.)
- Brand badge on image
- Score pill (green) with match percentage
- Price in NPR (bold blue, prominent)
- Spec tags: RAM, Storage, GPU, CPU, OS, Screen, Weight, Touchscreen
- Reason tags (green) / penalty tags (orange)
- "Best Match" gradient badge on #1 result
- Hover: lift + blue border + shadow

### 11.4 Colour & Contrast
- Strong primary blue for buttons, headings, accents
- High-contrast text (#0f172a on white)
- No pastel/faded elements
- Buttons wider than tall (0.55rem vertical, 2.5rem horizontal padding)
- Clear selected states via border + background + glow

### 11.5 Files Modified
- `ui/app.py` — Complete rewrite with hero, stats bar, step flow, horizontal product cards, brand-coloured laptop SVGs
- `ui/static/style.css` — Complete rewrite with royal blue/violet palette, strong shadows, e-commerce card layout, responsive breakpoints

### 11.6 Responsive
- Desktop: horizontal product cards, 3-col purpose grid, 4-col stats
- Tablet: stacked cards, 2-col grids
- Mobile: full-width cards, 2-col purpose grid

---

## Step 12: React Frontend (21.md)

**Date:** 2026-08-21
**Status:** Completed (Phases 1–3 of 21.md; Phases 4–5 pending)

### What Was Done
Replaced the Streamlit UI as the primary frontend with a React + Vite app in a new `frontend/` directory, while keeping the FastAPI backend, `model/recommend.py`, and dataset completely untouched (only additive CORS config was added to the API).

### 12.1 Environment Setup
- Windows Node.js (via WSL interop) could not operate on Linux filesystem paths — installed native Linux Node v24.19.0 to `~/.local/lib/node` with symlinks in `~/.local/bin` (no sudo required)
- Scaffolded Vite + React 19 project: `npm create vite@latest frontend -- --template react`

### 12.2 New Files (`frontend/`)
| File | Purpose |
|------|---------|
| `index.html` | Entry page — title, meta, Plus Jakarta Sans font |
| `vite.config.js` | Dev proxy `/api → http://localhost:8000` (avoids CORS in dev) |
| `src/styles/index.css` | Design system: palette tokens, reset, buttons, typography |
| `src/data/options.js` | Purposes/budgets/RAM/storage/CPU-GPU tiers mapped 1:1 to backend enums |
| `src/services/api.js` | Fetch wrappers for all 5 API endpoints with error handling |
| `src/components/Navbar.jsx/.css` | Sticky blur navbar, mobile hamburger menu |
| `src/components/Hero.jsx/.css` | Headline + CSS laptop mockup + floating spec chips + live stats |
| `src/components/PurposeGrid.jsx/.css` | 10 selectable purpose cards (matches ALL_PURPOSE_LABELS) |
| `src/components/BudgetSelector.jsx/.css` | Preset chips + gradient slider, NPR formatted (en-IN) |
| `src/components/PreferencesPanel.jsx/.css` | Chip groups for RAM/storage/CPU/GPU tiers, brand select (live from /brands), touchscreen & dedicated GPU toggles |
| `src/components/FinderSection.jsx/.css` | Orchestrates steps 1-2-3, builds payload, calls POST /recommend, error/loading states |
| `src/components/ResultsSection.jsx/.css` | Product cards: score pill, spec pills, reasons/penalties, Best Match badge on #1 |
| `src/components/Footer.jsx/.css` | Dark footer with links + "Ask AI coming soon" placeholder |

### 12.3 Backend Change (Additive Only)
- `api/main.py`: added CORSMiddleware allowing localhost origins (5173/3000/4173/8501) so the React frontend can call the API directly outside the dev proxy

### 12.4 Design System
- Warm light background (#faf7f1), deep blue primary (#2337b8), violet secondary (#7c3aed)
- Light theme only, strong contrast (#191d35 text), rounded cards, subtle shadows
- Hover lifts, staggered card entry animation, floating hero elements
- `prefers-reduced-motion` support, aria labels/aria-pressed on all controls

### 12.5 Amendments (same session, user feedback)
- **Multi-purpose selection:** purpose cards are now multi-select (toggle chips). Selected labels are joined with `" and "` (e.g. `Gaming and Programming`) — `parse_user_purpose()` keyword-scans the string and unions all matched labels, so combined purposes score correctly. Verified: `'Gaming and Programming'` → {Gaming, Programming}; `'Video Editing and Student'` → {Video Editing, Graphic Design, Student, General Use}
- **Hero floating chips fix:** added `z-index: 2` and moved badges to the visual's edges (`top:0/left:0`, `bottom:4%/left:-2%`, `top:16%/right:-2%`) so the laptop mockup no longer covers them; laptop width trimmed to `min(400px, 82%)`
- **View Details / Compare buttons:** intentionally non-functional placeholders for now — they belong to 21.md Phase 4 (details page) and Phase 5 (comparison view), which are the next planned steps. Buttons render with hover styles but have no click handlers yet.

### 12.6 Phase 4 — Product Details Modal
- **New:** `src/components/LaptopDetail.jsx/.css` — modal dialog (no routing library added) showing brand badge, name, price in NPR, match % score pill, full specification table (CPU/GPU + tiers, RAM, storage + type, display/touchscreen, OS, weight, suited-for), "Why it was recommended" list from engine `reasons`, "Things to consider" from engine `penalties` (with friendly empty state), disabled Ask AI placeholder and Compare button (Phase 5)
- **Wired:** App holds `detailRec` state; ResultsSection's View Details button opens the modal
- **Accessibility:** role=dialog + aria-modal, Escape/backdrop click closes, body scroll locked while open

### 12.7 Phase 5 — Comparison View
- **New:** `src/components/CompareTray.jsx/.css` — floating bottom tray appears when laptops are picked; shows selected brand chips, Clear button, and "⇄ Compare (n)" button (enabled at 2+, max 4)
- **New:** `src/components/CompareModal.jsx/.css` — side-by-side comparison table: Price, Match score, Processor, CPU tier, Graphics, GPU tier, Memory, Storage (+type), Display (+touch), Weight, OS, Suited for; sticky header row and label column; horizontal scroll on mobile
- **Best-value highlighting:** ★ marks the strict winner per row (lowest price & weight, highest score & specs); ties are intentionally not marked; legend included under the table
- **Wired:** card Compare buttons toggle selection with active state ("✓ Added", disabled at 4 max); LaptopDetail modal's Compare button adds to tray and closes; a new search clears the tray automatically
- Build ✓ · oxlint ✓

### 12.8 Verification
- `npm run build` ✓ · oxlint ✓ (no warnings)
- Live smoke test: uvicorn :8000 → POST /recommend ✓ → CORS preflight ✓ → Vite proxy /api/* ✓ → page serves ✓
- All smoke-test servers stopped after verification

### 12.9 How To Run
```bash
# Terminal 1 — API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# Terminal 2 — Frontend
cd frontend && npm run dev   # → http://localhost:5173
```
Streamlit app (`ui/app.py`) remains untouched and still works.

### 12.10 Session Handoff
- **New:** created `todo.md` at the project root — a resumable task list for future sessions
- Contains: completed-work checklist (Steps 1-12 / 21.md Phases 1-5), run commands, and the prioritized roadmap: UI polish -> click logging -> RAG -> LLM Ask-AI -> deployment -> nice-to-haves
- Includes guardrails: keep options.js purpose labels synced with ALL_PURPOSE_LABELS; do not rewrite backend/engine/dataset; Ask AI stays the only placeholder

### 12.11 Bug Fix — Card Compare Button
- **Bug:** clicking ⇄ Compare on a result card did nothing, while the same button inside the View Details modal worked
- **Cause:** `LaptopCard` (ResultsSection.jsx:32) received `onToggleCompare` from its parent but did not destructure it, so the onClick called `undefined`
- **Fix:** added `onToggleCompare` to the destructured props; build ✓ · oxlint ✓
- Reported by user during manual testing

---

## Step 13: UI Polish & QA (todo.md — NEXT UP #1)

**Date:** 2026-08-22
**Status:** Completed (one manual step left for the user)

### What Was Done
Step 1 of todo.md's roadmap: QA of multi-purpose combos, per-brand laptop images, and loading skeletons. Backend, `model/recommend.py`, and the dataset untouched.

### 13.1 Multi-Purpose Combo QA
Tested through the engine directly **and** the live API (`POST /recommend`):

| Combo | Budget | Top result | Verdict |
|-------|--------|------------|---------|
| Gaming and Programming | 100K | Infinix i9 + RTX 4060, 32GB (91.7%) | ✓ gaming GPU + strong CPU/RAM |
| Student and Office | 50K | Dell i5 + RTX 3050 @ 37.7K (79.7%) | ✓ budget all-rounders |
| Video Editing and Graphic Design | 150K | MSI i9 + RTX 4080 (93.9%) | ✓ creative-workstation class |
| AI / Machine Learning and Programming | 200K | MSI Ultra 9 + RTX 5080 (93.9%) | ✓ heavy compute |

Purpose parsing unions labels correctly (`Gaming and Programming` → {Gaming, Programming}; `Student and Office` → {General Use, Office, Student}).

### 13.2 Per-Brand Laptop Images (`frontend/src/components/LaptopVisual.jsx`)
- Replaced the generic tinted SVG placeholder with a dedicated component rendering a distinct open-laptop illustration per brand
- **26 brand themes** covering every brand in `data/laptops_ml_ready.csv` (HP blue, Lenovo red, ASUS navy, MSI dragon-red, Apple space-grey, Razer green-on-black, Alienware cyan-on-black, etc.)
- Three silhouette variants: `classic` (default), `gaming` (angular lid, accent glow line, base vents — ASUS/MSI/Razer/Alienware/Gigabyte/AORUS), `ultra` (thin-bezel MacBook style)
- Brand wordmark on the lower screen bezel; HP gets its circular ring logo; camera dot on classic lids
- Unknown brands fall back to a hashed colour tint (old behaviour preserved)
- `ResultsSection.css`: removed the five now-unused `.laptop-visual--*` modifier classes

### 13.3 Loading Skeletons
- New `SkeletonCard` in `ResultsSection.jsx` — mirrors card layout (visual block, title/subtitle lines, score square, spec pills, reason lines, price/button)
- Shown as a 6-card grid while a search runs, with shimmer sweep animation (`sk-sweep`)
- `prefers-reduced-motion: reduce` disables the sweep
- Accessibility: grid has `role="status"` + `aria-label="Loading recommendations"`
- Section heading swaps to "Finding your best matches…" while searching
- State wiring: `App` owns `searching`; `FinderSection` calls new `onLoadingChange(true/false)` prop around the fetch; `ResultsSection` receives it as `loading`

### 13.4 Responsive Audit (code-side)
- Results grid breakpoints confirmed present: 3-col desktop → 2-col ≤1024px → 1-col ≤640px; card actions stack vertically on mobile
- ⚠️ Left for user: a quick manual resize pass in the browser (desktop + mobile widths) — cannot be automated from here

### 13.5 Verification
- `npm run build` ✓ · `npx oxlint src` ✓ (no warnings)
- Live smoke test: uvicorn :8000 → POST /recommend `{"purpose":"Gaming and Programming"}` ✓ returned sensible ranked results
- Test server stopped after verification

### 13.6 Bug Fix — Compare Table Had No Horizontal Scrollbar on Phones
- **Reported by user** during manual mobile testing (the one manual QA item left in Step 1)
- **First attempt:** added `min-width: 560px` to `.compare-table` so narrow screens overflow instead of squeezing columns; added `-webkit-overflow-scrolling: touch`
- **Still broken — real root cause found:** `.compare-scroll` is a flex child of `.compare-modal` (`display: flex`). Flex items default to `min-width: auto`, so the scroll container refused to shrink below the table's intrinsic width and overflowed the modal itself instead of scrolling internally
- **Fix:** `min-width: 0` on `.compare-scroll` (lets the flex child shrink so `overflow: auto` actually engages) + `overscroll-behavior: contain` (stops swipe gestures from scrolling the page behind the modal)
- Kept the "← swipe the table sideways →" hint shown only ≤640px (mobile scrollbars are overlay-style and invisible until touched)
- **Third layer (after user reported it still not working):**
  - **Mouse drag-to-scroll** via pointer events on `.compare-scroll` (`scrollRef` + `drag` ref, grab/grabbing cursors) — in desktop browsers and DevTools phone emulation there is no swipe gesture at all, so a mouse user had no way to pan the table; touch devices keep native panning (handler skips `pointerType === "touch"`)
  - Slim **always-visible scrollbar** (`scrollbar-width/color` + `::-webkit-scrollbar` rules) so sideways scrollability is visible without touching first
  - Explicit `touch-action: pan-x pan-y` on the scroll area
- **Fourth layer (user: "vertical scrollbar exists, horizontal doesn't"):** root cause of the *invisible* horizontal bar — `scrollbar-width: thin` / `scrollbar-color` on `.compare-scroll` make Chromium ≥121 ignore the custom `::-webkit-scrollbar` styling entirely and fall back to the native **overlay** scrollbar, which on phones only appears mid-scroll in that direction. Removed both standard properties (with an explanatory comment so they don't creep back) → styled 8px scrollbar is now always visible/laid out in Chrome/Edge/Safari; Firefox falls back to its default thin bar. Vertical worked all along simply because users scroll down naturally; horizontal needed the visible affordance
- **Fifth layer (user: "the scrollbar appears and goes away — why?"):** explained that this is *expected platform behaviour* — touch devices (iOS Safari, Android Chrome) use transient overlay scrollbars that fade out ~1s after scrolling stops, to maximise content space; CSS cannot force persistence on iOS. Since the flash itself proves horizontal scrolling works, the remaining problem was only discoverability → added a **permanent edge-cue** to `.compare-scroll`: soft blue shadows at both horizontal edges via the CSS-only `background-attachment: local/local/scroll/scroll` technique (cover gradients ride on top and hide each shadow once its edge is fully scrolled to). The table now always signals hidden content, scrollbar visible or not
- Verified shipped bundle contains all rules (`min-width:560px`, `min-width:0;overflow:auto`, thin scrollbar, `is-dragging`)
- Build ✓ · oxlint ✓
- ⚠️ Note for future sessions: the file-edit tooling intermittently served stale file views this session — always confirm with `cat`/`grep` on disk before re-applying edits

### 13.7 "Show More" Recommendations Reveal
- **Motivation:** user asked whether shoppers should choose the result count instead of the fixed 6. Decision: yes to more results, but via an e-commerce-style **"Show more" button** rather than a number picker (keeps the guided 3-step flow clean)
- `FinderSection.jsx`: fetches `top_n: 12` from POST /recommend (API already supported it)
- `ResultsSection.jsx`: shows first 6 cards; a ghost "Show more laptops (N more) ↓" button reveals +6 per click; count resets automatically on every new search
- Reset uses React's *adjust-state-during-render* pattern (`state.lastResults` identity check) instead of a `useEffect`, avoiding oxlint's `set-state-in-effect` cascading-render warning
- Skeleton grid now renders exactly `INITIAL_VISIBLE` placeholders for visual consistency
- New CSS: `.results__more` centered footer row under the grid
- Rationale for capping at 12: popular budgets match thousands of rows, but engine scores drop off sharply past rank ~10 — deeper lists would mostly show weak matches
- Build ✓ · oxlint ✓ (no warnings)

| Step | Description | Est. Effort | Status |
|------|-------------|-------------|--------|
| 1 | Data Exploration | Done | Completed |
| 2 | Data Preprocessing | Medium | Completed |
| 3 | ML Model | High | Completed |
| 4 | API | Medium | Completed |
| 5 | Visualization | Medium | Completed |
| 6 | UI (Original) | Medium | Completed |
| 7 | Testing | Medium | Completed |
| 8 | QA, Bug Fixes & Finalization | Medium | Completed |
| 9 | UI Redesign (design.md) | High | Completed |
| 10 | Optional Specs & Filters | Medium | Completed |
| 11 | UI Redesign (g.md — E-Commerce) | High | Completed |
| 12 | React Frontend (21.md) | High | Completed (all phases) |
| 13 | UI Polish & QA (todo.md #1) | Medium | Completed |
| 14 | Market Insights — Data Viz in Website | Medium | Completed |
| 15 | Click Logging (todo.md #2) | Medium | Completed |
| 16 | RAG + LLM Ask-AI (todo.md #3–4) | High | Completed (Step 16 RAG; Step 17 LLM) |
| 17 | LLM "Ask AI" Chatbot — local Ollama Mistral (todo.md #4) | High | Completed |

---

## Step 17: LLM "Ask AI" Chatbot — Local Ollama + Mistral (todo.md #4)

**Date:** 2026-08-24
**Status:** Completed

### What Was Done
Implemented todo.md roadmap item #4: the previously-disabled 🤖 Ask AI button in the product-details modal now opens a real chatbot. Instead of a cloud free tier (Groq/Gemini, as originally sketched in todo.md), the user chose **Ollama running locally on Windows with the mistral model already pulled** — zero API cost, zero keys, fully offline, which also satisfies "never expose the key in frontend" trivially. Pipeline per todo.md: user question → RAG retrieval (`model/rag.py`, dataset-grounded) → Mistral explains/cites → answer streams to the chat panel. `model/recommend.py` remains the source of truth; the LLM only explains what retrieval returns. Engine, dataset and existing endpoints untouched.

### 17.1 Network Setup — WSL ↔ Windows Ollama (the tricky part)
The project lives in WSL2 (NAT mode); Ollama runs on the Windows host. Out of the box the server listens only on Windows' `127.0.0.1:11434`, which WSL cannot reach.
- Diagnosed via `netstat.exe`: `TCP 127.0.0.1:11434 LISTENING` (ollama.exe), WSL networking mode `nat` (`wslinfo --networking-mode`)
- **Fix applied:** `setx OLLAMA_HOST 0.0.0.0` (persistent Windows user env var), killed `ollama app.exe`/`ollama.exe` via `taskkill.exe`, relaunched through `explorer.exe "<path>\ollama app.exe"` so it started with fresh registry env → server now binds all interfaces
- Verified from WSL: `curl http://<gateway-ip>:11434/api/version` → `{"version":"0.32.15"}`; `mistral:latest` confirmed present via `ollama.exe list`
- **Reboot-proof auto-detection in code:** the NAT gateway IP changes across reboots, so nothing is hardcoded. `model/llm.py` resolves the base URL at request time by probing, in order: `OLLAMA_BASE_URL` env override → `http://localhost:11434` (works if WSL switches to mirrored mode or Linux-native ollama) → default-route gateway IPs from `/proc/net/route` → resolv.conf nameserver IPs. First probe that answers wins and is cached; any connection failure resets the cache and re-probes next time.
- Security note: `OLLAMA_HOST=0.0.0.0` exposes Ollama on the LAN while set; acceptable for this home dev machine, revisit before any public deployment.

### 17.2 New Module `model/llm.py`
- **Client:** thin `httpx` wrapper over Ollama's `/api/chat` (no new dependencies). `chat(messages, options, stream)` for complete replies, `stream_chat()` generator yielding deltas, generous 240 s timeout for CPU inference
- **Prompt building (grounding):** `SYSTEM_PROMPT` locks the model to LaptopFinder Nepal rules — answer ONLY from provided data, cite exact brands/models/NPR prices, never invent laptops/specs/prices/stock, admit missing info, <120 words, NPR currency. `build_chat_messages(question, sources, history, focus_laptop)` assembles system prompt + trimmed history + numbered `[1] [2] …` retrieved spec-sheet documents (+ optional "user is currently viewing:" line) + question
- **Helpers:** `clean_history()` (last `MAX_HISTORY_TURNS=6` valid user/assistant turns only), `format_focus_laptop()` (one-line spec summary of the laptop open in the modal, tolerant of partial/garbage dicts), `default_options()` (`num_predict 320`, `temperature 0.4`, `num_ctx 2048`), `model_name()` (`OLLAMA_MODEL` env, default `mistral`), `is_available()`
- `LLMUnavailable` exception raised on unreachable server / failed requests (cache reset included)

### 17.3 New API Endpoints (`api/main.py`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ask-ai` | Grounded chatbot answer (RAG → LLM) as one JSON response |
| POST | `/ask-ai/stream` | Same pipeline, NDJSON event stream for the UI |

- **Request:** `question` (1–1000 chars), optional `history[]` (`role` Literal user/assistant + content validated by Pydantic), `top_n` 1–10 (default 5 grounding docs), `max_price`, `brand`, `laptop` (focus record from the detail modal)
- **`/ask-ai` response:** `status ok`, `answer`, `model`, `query`, `retrieved`, `sources[]` (rank/similarity/laptop/document), `elapsed_ms`
- **`/ask-ai/stream` events:** `{"type":"start","model",…,"sources":[…]}` → many `{"type":"delta","text":"…"}` → `{"type":"done","answer",…}` (or `{"type":"error","detail":…}`). Retrieval/validation happen *before* streaming starts so HTTP errors still surface normally
- **Errors:** blank question → 422; invalid history role/content → 422; index missing → 503 with `python3 -m model.rag` hint (reused from `/ask`); no laptops matched filters → 503; Ollama unreachable → 503 listing every probed URL + start instructions. Both endpoints listed in the root endpoint map

### 17.4 Frontend Wiring
- **`services/api.js`:** `askAI()` non-streaming wrapper + `streamAskAI(payload, onEvent, signal)` — fetch POST with `ReadableStream` reader, incremental NDJSON parsing with partial-line buffering, abort-signal support, friendly errors for backend-down vs HTTP details
- **New `AskAiPanel.jsx/.css`:** chat panel rendered inside the detail modal above the action buttons. Suggestion chips ("Is this good value…?" etc.) when empty, violet-gradient user bubbles / bordered assistant bubbles, three-dot typing indicator while waiting for first token, live text append during streaming, per-answer "📚 grounded on N dataset laptops" chip, error box with Retry/Dismiss, Enter-to-send input row (disabled while busy), auto-scroll, `role="log"` + `aria-live="polite"`, `prefers-reduced-motion` disables the indicator animation
- **`LaptopDetail.jsx`:** 🤖 Ask AI button enabled (gradient hover lift, badge flips `soon`→`beta`, `aria-expanded`) toggling the panel; panel keyed by laptop identity so switching laptops starts a fresh conversation; abort controller cancels any in-flight stream on unmount
- **`LaptopDetail.css`:** `.btn-askai` un-disabled (cursor/hover/active states)

### 17.5 Tests (+34 → 206 total)
New `tests/test_llm.py`, fully offline (httpx mocked, never touches the real server):
- Prompt construction: system rules present, numbered context docs, history ordering/truncation/invalid-role filtering, focus-laptop formatting incl. partial & garbage records
- Host resolution: `OLLAMA_BASE_URL` override first, localhost candidate + no duplicates, probe-and-cache behaviour, raises `LLMUnavailable` when nothing answers (connection errors survived), `is_available()` both ways, `OLLAMA_MODEL` env/default
- Chat generation: payload shape (model/messages/options/stream flag), reply text extraction, HTTP error → `LLMUnavailable` + cache reset, NDJSON stream parsed until `done` (post-done lines ignored), non-200 stream raises
- Endpoints (real small RAG index fixture like test_rag.py): happy-path shape, **grounding identity — every source (brand, price_npr) exists in the source CSV slice**, prompt actually contains retrieved docs/question/focus line/history turns, LLM-down → 503, no-match filters → 503, missing index → 503 rebuild hint, blank question/invalid history role → 422, stream events order start→delta*→done with joined answer + sources count, mid-stream failure → error event after headers sent, root lists both endpoints
- Note: `tests/test_recommend.py::TestPerformance::test_recommend_multiple_queries` (wall-clock <2 s assertion) flaked once under parallel load this session but passes consistently otherwise — pre-existing timing sensitivity, unrelated to these changes

### 17.6 Verification
- `python3 -m pytest tests/ -q` ✓ **206 passed** (172 existing + 34 new)
- `npm run build` ✓ · `npx oxlint src` ✓ (chunk-size warning pre-existing/recharts)
- **Live smoke against real Mistral (Windows-hosted Ollama 0.32.15):**
  - `POST /ask-ai` "Is the ASUS TUF gaming laptop good for university students?" → grounded answer correctly describing the retrieved TUF machines (powerful CPU + dedicated NVIDIA, premium pricing caveat); sources = 4 actual ASUS rows (286K–448K NPR matching dataset values); 14.2 s cold-ish CPU inference
  - `POST /ask-ai/stream` "best laptop for programming under 80k?" → `start`(3 HP/ASUS sources) → 111 `delta`s → `done`; answer cites exact specs/prices of an HP i7 @ 64,948 NPR; 6.1 s warm
  - Error path covered by tests (mocked); smoke servers stopped afterwards
- ⚠️ The long-running uvicorn on :8000 predates this session — restart it (`python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000`) to pick up the new endpoints

### 17.7 How To Use
```bash
# one-time Windows-side setup (already done): OLLAMA_HOST=0.0.0.0 + restart Ollama app
# optional overrides: OLLAMA_BASE_URL / OLLAMA_MODEL env vars for the API process

# Terminal 1 — API (restart if it was already running)
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# Terminal 2 — frontend
cd ~/garima/frontend && npm run dev   # → http://localhost:5173
```
Then: search → View Details → 🤖 Ask AI → ask about the laptop (or use suggestion chips).

### 17.8 Notes For Later
- First question after ~5 min idle reloads Mistral into RAM (~8 s extra latency on Windows side) — subsequent answers are fast; streaming keeps perceived wait low either way
- If answers ever need different tone/length: tweak `SYSTEM_PROMPT` / `default_options()` in `model/llm.py` only
- Swap-in point for bigger models: pull another tag in Ollama and set `OLLAMA_MODEL`; nothing else changes

## Step 18: Scroll-to-Top Button + Footer Copy Fix (LOGBOOK Step 18)

**Date:** 2026-09-08
**Status:** Completed

### What Was Done
Small UX/navigation polish + a stale-footer fix. Frontend only — backend, `model/recommend.py`, dataset, and all existing components untouched.

### 18.1 Scroll-to-Top Button
- **New:** `frontend/src/components/ScrollToTop.jsx/.css` — a floating circular button (gradient primary→violet, consistent with the design system) fixed bottom-right
- Appears only after the user scrolls past 400px (so it never crowds the hero CTA); clicking smooth-scrolls back to the top
- Hover lift + shadow, entry animation, `aria-label="Scroll to top"`, icon is an inline SVG chevron (no new dependency), `prefers-reduced-motion` disables the animation
- On mobile it sits a bit higher (above the compare tray zone) at 42px
- **Wired:** `App.jsx` renders `<ScrollToTop />` just before `<Footer />`

### 18.2 Footer Copy Fix
- **`Footer.jsx`:** "🤖 Ask AI coming soon" → "🤖 Ask AI live on every product" — Ask AI shipped back in Step 17, so the footer was stale/misleading

### 18.3 Verification
- `npm run build` ✓ · `npx oxlint src` ✓ (only the pre-existing >500 kB recharts chunk-size warning)
- No Python/backend changes, so no `pytest` impact; the existing 206 tests are unaffected

### 18.4 Files Changed
| File | Change |
|------|--------|
| `frontend/src/components/ScrollToTop.jsx` | **New** — floating scroll-to-top button |
| `frontend/src/components/ScrollToTop.css` | **New** — styles |
| `frontend/src/App.jsx` | Import + render `<ScrollToTop />` |
| `frontend/src/components/Footer.jsx` | Ask AI meta copy now says "live" |

---

### 18.5 HOW TO UNDO / REVERT (baseline restore)
This step adds **two brand-new files** and makes **two one-line edits** to existing files — all fully frontend, no git history is required to revert (the project is not under version control).

**To restore the exact pre-Step-18 state:**

1. **Delete the two new files**
   ```bash
   rm frontend/src/components/ScrollToTop.jsx
   rm frontend/src/components/ScrollToTop.css
   ```

2. **Revert `frontend/src/App.jsx`** — remove the two added ScrollToTop references:
   - Delete the import line: `import ScrollToTop from "./components/ScrollToTop";`
   - Delete the render line: `<ScrollToTop />` (the line right before `<Footer />`)

3. **Revert `frontend/src/components/Footer.jsx`** — change the meta line back to the original:
   - `🤖 Ask AI live on every product` → back to `🤖 Ask AI coming soon`

4. **Optionally clear the newly built bundle** (only if you ran a build):
   ```bash
   rm -rf frontend/dist
   ```

After steps 1–3 the UI is byte-for-byte identical to the state before this Step 18 (the button disappears and the footer reads "coming soon"). The backend engine, dataset, tests, and every other component are untouched by this step, so no further reverting is needed.

---

## Step 19: UX & Product Upgrades — Deals, Sort/Filter, Count-up, How It Works, Favorites, Shareable Links (LOGBOOK Step 19)

**Date:** 2026-09-08
**Status:** Completed

### What Was Done
A round of "bigger jump" improvements on top of the Step 18 baseline: deal highlighting in the engine, a sort/filter toolbar on results, animated hero stats, a how-it-works explainer, a browser-stored saved list, and shareable/bookmarkable search URLs. Backend engine, dataset, and the existing 206 tests remain intact (all still pass).

### 19.1 Deal Detection (backend)
- **`model/recommend.py`:** new `_deal_context(laptops)` builds per-segment price medians (`(cpu_tier, gpu_tier, ram_band)` bucket → median price, global-median fallback); new `_classify_deal(laptop, ctx)` returns `(is_deal, tier, note)` where `tier` is `great` (price ≤ 0.85×median), `good` (≤ 0.97×), `fair` (≤ 1.1×), else `premium` (overpriced)
- `recommend()` now annotates every returned row with `deal: {is_deal, tier, note}` — both the main top-N path and the `no_exact_match` fallback path (via a shared `_annotated()` helper)
- **`api/main.py`:** added `class DealOut(BaseModel): is_deal, tier, note` and `Recommendation.deal: DealOut = None` — **required** because FastAPI's `response_model` strips undocumented fields from the JSON response
- Verified live through the HTTP layer with a TestClient call (deal field now visible in `/recommend`)
- Full suite **206 tests pass** (99 in test_recommend.py)

### 19.2 Sort / Filter Toolbar on Results
- **`frontend/src/components/ResultsSection.jsx`** rewritten: a toolbar above the results grid with sort chips (`Best match` ranked, `Price: low→high`, `Price: high→low`, `RAM ↑`, `Storage ↑`), a `🏷️ Deals only` toggle (shows the badge count of great-deal laptops), and a live "X laptops" results counter
- New `DealBadge` component (`great`/`good`/`premium` variants) + "Light" weight badge, `fav-btn` heart toggle on each card, `SkeletonCard` loading shells, "Show more" paging (initial visible 6, step +6), and automatic reset of sort/filter/page whenever a new search lands
- Styles appended to `ResultsSection.css` (toolbar, chips, deals button, badges, heart, info row)

### 19.3 Animated Stat Count-up (Hero)
- **New** `frontend/src/hooks/useCountUp.js` — rAF-driven counter with `easeOutCubic`, formats whole numbers, and runs instantly when `prefers-reduced-motion` is set
- **`Hero.jsx`** uses it for the laptop-count and brand-count stats instead of static text

### 19.4 "How It Works" Explainer
- **New** `frontend/src/components/HowItWorks.jsx/.css` — a 3-step strip (Tell us → We rank → You compare) shown once, between the hero and the finder
- Wired into `App.jsx` between `<Hero>` and `<FinderSection>`

### 19.5 Favorites / Saved List
- **New** `frontend/src/services/favorites.js` — localStorage-backed helper (`laptopfinder.favorites.v1`): stable `favoriteId` from brand|cpu|ram|storage|price, `getFavorites`, `toggleFavorite`, `isFavorited`, `clearFavorites`; stored objects now keep `reasons`/`penalties` so saved items open fully in the detail modal
- **New** `frontend/src/components/FavoritesSection.jsx/.css` — "Laptops you saved for later" grid with View / Remove / Clear-all
- Card hearts in `ResultsSection` + a `Save` button in the `LaptopDetail` modal (green "Saved" state); `App.jsx` owns `favorites` state and passes `favorites`/`onToggleFavorite` down; detail modal handles saved items that may lack `reasons`/`penalties`

### 19.6 Shareable / Bookmarkable Search URLs
- **`FinderSection.jsx`:** `formFromUrl()` hydrates the form from the query string on load; `syncUrl()` writes the form into the URL via `history.replaceState` after each successful search (so back/forward stays clean); `Reset` clears the params; a shared link with `purpose=` auto-runs the search once on mount
- Small "your filters are saved to the link" hint under the actions

### 19.7 Verification
- `npm run build` ✓ · `npx oxlint src` ✓ (only the pre-existing >500 kB recharts chunk-size warning + one intentional `setState`-in-effect note in the count-up hook)
- `python3 -m pytest tests/ -q` → **206 passed**

### 19.8 Files Changed (this step)
| File | Change |
|------|--------|
| `model/recommend.py` | **Modified** — `_deal_context`, `_classify_deal`, `_annotated`; `deal` field on every recommendation |
| `api/main.py` | **Modified** — `DealOut` model; `Recommendation.deal` field (FastAPI response_model safety) |
| `frontend/src/components/ResultsSection.jsx` | **Rewritten** — sort/filter toolbar, DealBadge, favorites heart, skeleton, show-more |
| `frontend/src/components/ResultsSection.css` | **Modified** — toolbar/chip/badge/heart styles |
| `frontend/src/hooks/useCountUp.js` | **New** — animated counter hook |
| `frontend/src/components/Hero.jsx` | **Modified** — count-up stats |
| `frontend/src/components/HowItWorks.jsx` | **New** — explainer strip |
| `frontend/src/components/HowItWorks.css` | **New** |
| `frontend/src/services/favorites.js` | **New** — localStorage saved list |
| `frontend/src/components/FavoritesSection.jsx` | **New** — saved-laptops grid |
| `frontend/src/components/FavoritesSection.css` | **New** |
| `frontend/src/components/LaptopDetail.jsx` | **Modified** — Save button, tolerant of saved items without reasons/penalties |
| `frontend/src/components/LaptopDetail.css` | **Modified** — saved-state styling |
| `frontend/src/components/FinderSection.jsx` | **Modified** — URL state read/write + auto-run on shared links |
| `frontend/src/components/FinderSection.css` | **Modified** — share hint |
| `frontend/src/App.jsx` | **Modified** — HowItWorks, FavoritesSection, favorites state + wiring |

---

### 19.9 HOW TO UNDO / RESTORE TO ORIGINAL (baseline restore)
The exact pre-Step-19 state (i.e. the project "as it was" when this step started, including Step 18) is archived in the snapshot folder:
`.baseline_snapshot_2026-09-08_before_step19_improvements/`

The project is **not under git**, so restoring means copying the snapshot back over the working files. The snapshot contains `model/`, `api/`, `ui/`, `tests/`, `visualization/`, `frontend/src`, frontend config files, the data CSV, and all top-level docs — everything except `node_modules/` and the regenerable `data/chroma/` index.

**Option A — full restore (files changed by this step only):**
1. Back up anything you want to keep in the working tree first (e.g. `cp -r frontend/src /tmp/opencode/src_step19`).
2. Copy the archived files back:
   ```bash
   cd /home/garimadangol/garima
   cp -r .baseline_snapshot_2026-09-08_before_step19_improvements/model/.  model/
   cp -r .baseline_snapshot_2026-09-08_before_step19_improvements/api/.     api/
   cp -r .baseline_snapshot_2026-09-08_before_step19_improvements/frontend/. frontend/
   cp -r .baseline_snapshot_2026-09-08_before_step19_improvements/tests/.   tests/
   cp -r .baseline_snapshot_2026-09-08_before_step19_improvements/visualization/. visualization/
   cp    .baseline_snapshot_2026-09-08_before_step19_improvements/data/laptops_ml_ready.csv data/
   cp    .baseline_snapshot_2026-09-08_before_step19_improvements/LOGBOOK.md LOGBOOK.md
   cp    .baseline_snapshot_2026-09-08_before_step19_improvements/todo.md todo.md
   cp    .baseline_snapshot_2026-09-08_before_step19_improvements/summary.md summary.md
   cp    .baseline_snapshot_2026-09-08_before_step19_improvements/design.md design.md
   cp    .baseline_snapshot_2026-09-08_before_step19_improvements/instruct.md instruct.md
   ```
3. `node_modules` is not snapshotted, so refresh it (nothing changes functionally):
   ```bash
   cd /home/garimadangol/garima/frontend && npm install && npm run build
   ```
4. Verify: `cd /home/garimadangol/garima && python3 -m pytest tests/ -q` → 206 passed, plus a clean vite build.

**Option B — selective revert (per feature), for a lighter touch:**
- **Deal detection off:** in `api/main.py` delete the `deal: DealOut = None` line from `Recommendation` (field no longer serialized); restore `recommend.py` from the snapshot if you want the engine functions gone too.
- **Sort/filter toolbar off:** restore `ResultsSection.jsx` + `.css` from the snapshot and remove the `favorites`/`onToggleFavorite` props from its usage in `App.jsx`.
- **Count-up off:** restore `Hero.jsx`; delete `frontend/src/hooks/useCountUp.js`.
- **How-it-works off:** delete `HowItWorks.jsx/.css`; remove its render+import in `App.jsx`.
- **Favorites off:** delete `favorites.js`, `FavoritesSection.jsx/.css`; remove favorites state/wiring in `App.jsx`, the heart in `ResultsSection`, and the Save button in `LaptopDetail.jsx` (restore both files from the snapshot for a clean result).
- **URL-state on:** revert `FinderSection.jsx`/`.css` from the snapshot (keep `handleFind`/`reset` original) — the URL stays clean because the query-string code is gone.

**Source of truth:** `.baseline_snapshot_2026-09-08_before_step19_improvements/` — copy any file out of it to restore the exact pre-Step-19 original. Rebuild (`npm run build`) if you want the shipped bundle updated.

---

### 19.10 Ask AI doesn't re-describe the laptop before answering (follow-up fix)
**Date:** 2026-09-08 · **Status:** Completed

**Problem:** When a user asked something like "is this a reasonable price for the quality?", the assistant first echoed a short recap of the laptop's specs (which the user already sees on screen) and only answered the actual question in a later paragraph.

**Fix:** `model/llm.py` `SYSTEM_PROMPT` — added an explicit rule: the laptop specs and price are already visible on the user's screen, so the model must **not repeat or re-describe them** and must answer the question in its first sentence. The focus-laptop spec line is still fed as grounding context (so the model has the facts), but it is told not to narrate it back.

**Verification:** `tests/test_llm.py` — extended `test_system_prompt_present_with_grounding_rules` to assert the new instruction is in the system prompt. Full suite: **206 passed**. Frontend unchanged (no rebuild needed).

---

## Step 20: Ask AI Chatbot Upgrade — Grounding Viz, Follow-up Memory, UX Polish (Item 2)

**Date:** 2026-09-08
**Status:** Completed

### What Was Done
Item 2 of the follow-up plan: make the Ask AI chatbot visibly *grounded*, memory-aware on follow-ups, and nicer to use. Builds directly on the 19.10 fix.

### 20.1 Show Retrieved Sources (the big one)
- **`frontend/src/components/AskAiPanel.jsx`** (rewritten): the `start` stream event already carried the full `sources` array; the panel now stores it per message and renders **clickable source chips** (brand · CPU model · NPR price) under each grounded answer
- Clicking a chip opens that laptop's own detail view: `App.jsx` gained `openAskAiSource(src)` (logs `view_source` + builds a minimal rec), threaded as `onViewLaptop` through `LaptopDetail` → `AskAiPanel`
- Typing state now also says "reading N dataset laptops…" once sources arrive
- `AskAiPanel.css`: added `.askai__citations`, `.askai__cite`, `.askai__rich`, `.askai__thinking` styles

### 20.2 Rich (markdown-lite) Answers
- New `renderRichText()` in `AskAiPanel.jsx`: renders `**bold**`, bullet lists (`-`/`•`/`*`) and numbered lists as proper elements — no `innerHTML`, React nodes only (no XSS surface)

### 20.3 Follow-up Memory
- **`model/llm.py`** `SYSTEM_PROMPT`: added a rule that short follow-ups ("and this one?", "is the cheaper one better?") refer to laptops already discussed / currently viewed, not a brand-new search. History is already re-supplied per request.

### 20.4 Smarter Suggestions + Friendlier Errors
- `suggestionsFor(laptop)` builds intro chips matched to the laptop (gaming GPU → "How does it handle modern games?", video-editing CPU → "powerful enough for video editing?", student/budget → college-work question, business → office-work question), falling back to the four generic prompts
- `friendlyError()` turns raw Ollama/server errors into one clear line: "The AI is offline — make sure Ollama is running, then hit Retry."

### 20.5 Files Changed
| File | Change |
|------|--------|
| `model/llm.py` | **Modified** — SYSTEM_PROMPT gains follow-up-memory rule |
| `frontend/src/components/AskAiPanel.jsx` | **Rewritten** — sources chips, rich text, per-laptop suggestions, typing polish, friendly errors |
| `frontend/src/components/AskAiPanel.css` | **Modified** — new chip/rich/thinking styles |
| `frontend/src/components/LaptopDetail.jsx` | **Modified** — passes `onViewLaptop` to AskAiPanel |
| `frontend/src/App.jsx` | **Modified** — `openAskAiSource`, wires `onViewLaptop` into LaptopDetail |
| `tests/test_llm.py` | **Modified** — asserts follow-up rule present |

### 20.6 Verification
- `python3 -m pytest tests/ -q` → **206 passed**
- `npm run build` ✓ · `npx oxlint src` ✓ (only the pre-existing chunk-size warning + intentional count-up effect note)

### 20.7 HOW TO UNDO / REVERT
- **Backend:** restore `model/llm.py` from `.baseline_snapshot_2026-09-08_before_step19_improvements/` (or delete the added "Short follow-ups…" rule from `SYSTEM_PROMPT`)
- **Frontend:** restore `AskAiPanel.jsx/.css`, `LaptopDetail.jsx`, and `App.jsx` from the same snapshot. `App.jsx` also contains Step-19 wiring, so to revert only Item 2, remove the `openAskAiSource` function + its `onViewLaptop` prop and drop the AskAiPanel/AskAiPanel.css changes (the snapshot's copies are pre-Item-2 but post-Step-19, so restoring just these four files cleanly undoes this step).
- Rebuild after reverting frontend files: `cd frontend && npm run build`.

---

## Step 16: RAG Retrieval — ChromaDB Vector Search over the Dataset (todo.md #3)

**Date:** 2026-08-23
**Status:** Completed

### What Was Done
Implemented todo.md roadmap item #3 — deliberately *before* any LLM work. All 5,284 laptops are now indexed into a local ChromaDB vector collection, and a new `GET /ask` endpoint answers free-text questions ("lightweight laptop for students under 50k") by retrieving real laptops from OUR dataset. Grounding is structural, not prompt-based: only indexed dataset rows can ever be returned, so prices/models cannot be hallucinated. Engine, dataset and existing endpoints untouched.

### 16.1 New Module `model/rag.py`
- **Vector store:** ChromaDB `PersistentClient` at `data/chroma/` (collection `laptops`, cosine space, anonymized telemetry disabled)
- **Documents:** every laptop becomes a readable natural-language spec sheet, e.g.
  `"ASUS Intel laptop. Core i7-11370H processor (fast performance CPU, tier 4 of 6). GeForce RTX 3070 ... dedicated NVIDIA graphics suitable for gaming, tier 5 of 6. 16GB RAM. ... priced at NPR 57,999 (mid-range). suited for Gaming."`
  Descriptors reuse the engine's own tier functions (`cpu_tier`/`gpu_tier`) plus price-bracket words (budget / affordable / mid-range / premium / flagship) and weight words (ultralight / lightweight), so free-text queries match lexically
- **Metadata = full formatted record** (`format_laptop()` shape) stored per document → answers are grounded without re-reading the CSV, and the future LLM can quote fields safely
- **Embeddings:** scikit-learn TF-IDF (4,000 features, word 1–2 grams) fitted once at build time; vectors stored *directly* in Chroma; fitted vectorizer pickled alongside (`vectorizer.pkl`) + build stats in `index_meta.json`
- **Budget-phrase extraction:** regex pulls price caps out of the query text — "under 80k" → 80,000; "below 1 lakh" → 100,000; "up to 50 thousand"; bare "under 60" → 60,000; an explicit `max_price` parameter overrides it
- **Filters:** optional `brand` equality and/or `price_npr ≤ max_price`, combined into Chroma `$and` where-filters when both present
- **Module API:** `build_index(data_path=None, persist_dir=None)`, `ask(query, n_results=5, max_price=None, brand=None)`, `set_index_dir(path)` / `reset_index_dir()` for test isolation (mirrors `interactions.set_db_path()`), `extract_budget_hint(query)`; heavy imports (chromadb/sklearn/numpy) are lazy so importing the module stays cheap
- **Rebuild CLI:** `python3 -m model.rag` rebuilds the index and runs four demo queries

### 16.2 New API Endpoint (`api/main.py`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ask` | Free-text Q&A search over the dataset (RAG retrieval, grounded answers) |

- **Params:** `query` (required), `top_n` 1–20 (default 5), `max_price` (optional NPR cap, overrides query phrase), `brand` (optional exact filter)
- **Response:** `status` (`ok` / `no_match`), `message`, `query`, `total_indexed`, `max_price_applied`, `answers[]` with `rank` / `similarity` (cosine, rounded) / `distance` / `laptop` (full record) / `document` (indexed spec sheet — grounding source for the LLM step)
- **Errors:** missing/blank `query` or out-of-range `top_n` → 422; index not built → 503 whose detail says to run `python3 -m model.rag`; listed in the root endpoint map
- ⚠️ **FastAPI gotcha hit:** installed fastapi 0.141.1 + pydantic 2.13.4 reject plain `pydantic.Field(...)` defaults on query params (`non-body parameters must be in path, query, header or cookie`) — params must use `fastapi.Query(...)`

### 16.3 Tests (+29 → 172 total)
New `tests/test_rag.py` (module-scoped fixture builds a throwaway 150-row index from a spread-out slice of the real CSV):
- Budget-hint extraction: 6 unit tests (k/lakh/thousand/bare-number/no-phrase)
- Document builder: 3 tests (brand+CPU present, tier + NPR + suited-for wording, unknown weight/storage handled)
- Index building: 4 tests (row count matches slice, meta file written, rebuild idempotent, helpful FileNotFoundError when index dir empty)
- Retrieval: 10 tests (ranks/similarity ordering, **grounding identity — every answer's (brand, price) must exist in the source CSV**, max-price & brand filters, budget hint applied end-to-end + explicit override, impossible-filter no_match status, blank-query ValueError, n_results clamped to collection size and API max)
- API integration: 6 tests (happy path shape, 422 missing/blank query, 422 bad top_n, 503 with rebuild hint when index missing, root lists endpoint)

### 16.4 Verification
- `python3 -m pytest tests/ -q` ✓ **172 passed** (143 existing + 29 new)
- Real index built: `python3 -m model.rag` → 5,284 laptops indexed (dim=4000) into `data/chroma/` (~2s build); demo queries returned sensible results (gaming→RTX machines, macbook→Apples, budget phrases applied)
- Live smoke: uvicorn :8000 → GET `/ask?query=gaming laptop under 80k&top_n=3` ✓ grounded JSON with `max_price_applied: 80000`; edge cases ✓ (missing/blank query → 422, top_n=99 → 422, brand+max_price combo ✓, impossible filters → `no_match`)
- Latency: ~11 ms per /ask request (warm)
- Test server stopped afterwards

### 16.5 How To Use
```bash
# one-time (or after any dataset change)
python3 -m model.rag

# then ask away
curl "http://localhost:8000/ask?query=lightweight%20laptop%20for%20students%20under%2050k&top_n=3"
```

### 16.6 Upgrade Path (note for the LLM step)
Embeddings currently use TF-IDF vectors stored directly in Chroma — deterministic, offline, zero downloads. If semantic fuzziness is needed later (synonyms, paraphrases), swap in MiniLM/BGE by replacing the vectorizer calls in `_load_index()`/`build_index()` with an embedding-function call; `model/rag.ask()`'s interface and the metadata-grounding design stay unchanged.

---

---

## Step 14: Market Insights — Interactive Data Visualization on the Website

**Date:** 2026-08-23
**Status:** Completed

### What Was Done
Moved data visualization from static matplotlib PNGs into the React website as live, interactive charts fed by a new API endpoint. Backend changes are additive only (`get_insights()` + one endpoint); engine, dataset and existing endpoints untouched.

### 14.1 New `GET /insights` Endpoint
- **`model/recommend.py` → `get_insights(data_path=None)`** — additive function mirroring `get_dataset_stats()`. Returns:
  - `price_histogram`: NPR 10K buckets up to 200K + open "200K+" bucket; leading empty buckets trimmed; counts cover every positive-priced laptop exactly (5,284)
  - `top_brands`: top 10 brands by laptop count
  - `purpose_distribution`: all 10 purpose labels, descending
  - `ram_vs_price`: avg price per RAM size; rare configs (<20 laptops, e.g. 18GB×1, 192GB×7) filtered so charts stay readable
  - `cpu_tier_distribution` / `gpu_tier_distribution`: fixed tiers 1–6 via existing `cpu_tier()`/`gpu_tier()`
  - `storage_type_distribution`: SSD/HDD/etc. counts, descending
- **`api/main.py`**: Pydantic response models (`InsightsResponse`, `Bucket`, `BrandCount`, `RamPrice`, `TierCount`, etc.) + `GET /insights` endpoint + listed in root endpoint map

### 14.2 React Insights Section
- **Dependency:** added `recharts` (~39 packages)
- **New:** `frontend/src/components/InsightsSection.jsx/.css` — self-fetching section rendered below ResultsSection (`id="insights"`):
  | Chart | Type | Notes |
  |-------|------|-------|
  | Price landscape | AreaChart (wide card) | gradient fill, dashed violet cursor, band-start tick labels |
  | Top brands | horizontal BarChart | value labels right of bars |
  | Purpose split | horizontal BarChart | truncated category ticks |
  | RAM vs avg price | BarChart | violet gradient, compact NPR axis ("1.5L"/"80K") |
  | CPU vs GPU power mix | grouped BarChart | custom two-dot legend |
  | Storage types | donut PieChart | total-laptop count centred in hole, colour-dot legend |
- Styled with design tokens (#2337b8/#7c3aed palette, white cards, radius/shadow vars); custom tooltip component shows full NPR prices and sample-size sub-lines
- Loading state: shimmer skeleton grid; error state: friendly box with Try Again button (retry token pattern — no synchronous setState in effect, keeps oxlint happy)
- `prefers-reduced-motion` disables chart animations + skeleton sweep
- Wired: `App.jsx` renders `<InsightsSection />`; Navbar gains "Insights" link; Footer gains "Market Insights" link; `services/api.js` gains `getInsights()`

### 14.3 Tests (+14 → 135 total)
- `tests/test_recommend.py::TestGetInsights` — 8 unit tests (totals match stats, histogram covers all priced laptops, buckets ordered, brands sorted/capped, tiers 1–6 complete, RAM sorted & min-count filtered, storage types present, <2s performance)
- `tests/test_api.py::TestInsightsEndpoint` — 6 integration tests (payload shape, histogram sum == positive-price count, brands sorted ≤10, RAM filter honoured, root lists endpoint)

### 14.4 Verification
- `python3 -m pytest tests/ -q` ✓ 135 passed
- `npm run build` ✓ (616 modules) · `npx oxlint src` ✓ (no warnings)
- Live smoke: uvicorn :8000 → GET /insights ✓ full JSON · Vite dev proxy `localhost:5173/api/insights` ✓ same payload
- Test servers stopped afterwards

### 14.5 Session Notes
- ⚠️ The stale-file-view tooling bug from LOGBOOK 13.6 recurred and was worse: edits intermittently double-applied (duplicate imports/renders appeared on disk while tools reported success). Workaround that held: verify every touched file with `grep` immediately after editing, prefer full-file `write` over incremental `edit` for affected files, and de-duplicate before building. Files confirmed clean at end of session: App.jsx, Navbar.jsx, Footer.jsx, api.js, InsightsSection.jsx/.css, model/recommend.py, api/main.py, both test files.

---

## Step 15: Click Logging — Interaction Data for Future ML (todo.md #2)

**Date:** 2026-08-23
**Status:** Completed

### What Was Done
Implemented the todo.md #2 roadmap item: every search and user click is now persisted to SQLite so future sessions can train real ML models (collaborative filtering / learning-to-rank) on what users actually open, not just what scores highest. Engine, dataset and existing endpoints untouched.

### 15.1 New Module `api/interactions.py`
- **Storage:** `data/interactions.db` (SQLite, WAL mode, thread-lock + per-call connections; FastAPI sync endpoints run in a threadpool)
- **Schema:**
  - `search_events` — ts, client_sid (frontend UUID per search), full query params (budget, purpose, min_ram/storage/type, brand, cpu/gpu tiers, min_screen, touchscreen, dedicated_gpu, top_n), engine status, results_shown count, top_score
  - `click_events` — ts, client_sid (joins to search), search_row_id (nullable FK), action (`view_details` | `compare_add` | `compare_remove` | `show_more`), position (0-based rank), score, laptop identity (brand, CPU/GPU model, RAM, storage + type, price, OS, screen)
- **Helpers:** `insert_search()`, `insert_click()`, `log_stats()` (totals + by-action + last 10 clicks), `export_json()` (full dump for offline ML notebooks), `set_db_path()` (test isolation)

### 15.2 New API Endpoints (`api/main.py`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/log-search` | Log a search + results shown → `{status:"logged", id}` |
| POST | `/log-click` | Log an interaction; `action` validated via Pydantic `Literal` (422 on unknown) |
| GET | `/logs/stats` | Totals, clicks-by-action, 10 most recent clicks |

All listed in the root endpoint map. Logging endpoints are intentionally separate from `/recommend` so analytics failures can never affect recommendations.

### 15.3 Frontend Wiring (fire-and-forget, never breaks UX)
- **`services/api.js`:** `beginSearch()` generates a UUID per search (kept in module state); `logSearch(payload, data)` posts query params + status + results_shown + top_score; `logClick(action, rec?, extra?)` posts laptop identity + rank from `rec._rank`; all `.catch(() => null)` — silent failure
- **`FinderSection.jsx`:** each "Find My Laptop" run calls `beginSearch()`, stamps results with `_rank` (1-based) and `_sid`, then fires `logSearch`
- **`App.jsx`:** new `openDetails()` wrapper logs `view_details`; `toggleCompare()` logs `compare_add`/`compare_remove` — central placement covers BOTH card buttons and the detail-modal compare button
- **`ResultsSection.jsx`:** "Show more" logs `show_more` with the reveal position
- No PII collected — only product/spec interaction data

### 15.4 Tests (+8 → 143 total)
`tests/test_api.py::TestLoggingEndpoints` with a `temp_log_db` fixture (monkeypatches the DB path to a tmp file per test): search ids increment, defaults accepted, view_details payload round-trips, all four actions valid, unknown/missing action → 422, stats counts correct, root lists endpoints.

### 15.5 Verification
- `python3 -m pytest tests/ -q` ✓ 143 passed
- `npm run build` ✓ · `npx oxlint src` ✓
- Live smoke: uvicorn :8000 → POST /log-search ✓, POST /log-click ×3 (view_details with full laptop payload, compare_add, show_more) ✓, GET /logs/stats ✓ returned correct totals + recent rows; SQLite dump confirmed schema and data
- Smoke-test rows deleted afterwards — user starts with a clean DB

### 15.6 How To Inspect Logged Data Later
```bash
curl http://localhost:8000/logs/stats                 # quick summary
python3 -c "from api.interactions import export_json; print(export_json())"   # full ML-ready dump
```

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-19 | Use Price_NPR as primary price column | Dataset is Nepal-focused |
| 2026-08-19 | Drop Warranty, IPS_Panel columns | >50% missing values |
| 2026-08-19 | Content-based scoring approach | No user interaction data available |
| 2026-08-19 | 6-tier CPU/GPU scoring system | Covers full range from Celeron to i9/M-series |
| 2026-08-19 | 35/25/35/5 weight split | Budget+Specs most important, purpose meaningful, balance minor |
| 2026-08-19 | No ML training required | Score-based engine; no labeled data to train on |
| 2026-08-20 | Handle missing values at runtime with defaults | Keeps raw CSV intact; defaults (0/Unknown) work well for ranking |
| 2026-08-20 | 121 tests across unit/API/E2E layers | Comprehensive coverage: all endpoints, scoring logic, edge cases |
| 2026-08-20 | Fixed RTX 3050 GPU tier pattern | Missing pattern `"geforce rtx 3050"` caused incorrect tier 1 classification |
| 2026-08-20 | Explicit None check for budget | `or 0` is insufficient; used `_budget if _budget is not None else 0` |
| 2026-08-20 | UI redesign: guided step flow | design.md required card-based UX instead of sidebar-heavy layout |
| 2026-08-20 | Muted teal accent (#5b8a8a) | Accessible, calming, distinctive — avoids neon/blue overuse |
| 2026-08-20 | Replaced OS filter with Dedicated GPU | 1,001/5,284 laptops have unknown OS, making it a bad filter |
| 2026-08-20 | Dynamic spec display (no more N/A) | Shows known specs and skips unknowns instead of displaying "N/A" |
| 2026-08-20 | g.md e-commerce redesign | Reverted design.md direction; rebuilt as polished laptop shopping site with royal blue primary, horizontal product cards, laptop SVG imagery, hero gradient |
| 2026-08-21 | React replaces Streamlit as primary UI | 21.md decision; e-commerce-grade UX not achievable in Streamlit; backend untouched |
| 2026-08-21 | Vite dev proxy `/api → :8000` + CORS middleware | Proxy removes CORS friction in dev; CORS keeps direct calls working in other setups |
| 2026-08-21 | Native Linux Node in ~/.local (no sudo) | Windows node.exe via WSL interop cannot operate on Linux filesystem paths |
| 2026-08-21 | Purpose labels mirrored in `src/data/options.js` | Frontend options must stay in sync with ALL_PURPOSE_LABELS / tier scales in recommend.py |
| 2026-08-22 | Per-brand SVG illustrations instead of stock photos | Zero external assets/licensing; distinct silhouettes (classic/gaming/ultra) + brand colours cover all 26 dataset brands |
| 2026-08-22 | Skeletons driven by App-level `searching` state | FinderSection stays self-contained; ResultsSection only needs a boolean `loading` prop |
| 2026-08-23 | Interactive Recharts over static PNGs for the website | Live charts via GET /insights demonstrate Python+ML+API+Viz end-to-end and match the design system; matplotlib charts kept for reports |
| 2026-08-23 | RAM-vs-price groups filtered to ≥20 laptops | Rare configs (18GB×1, 192GB×7) made averages noisy; threshold keeps chart readable |
| 2026-08-24 | Local Ollama + Mistral for Ask AI instead of cloud Groq/Gemini | User's choice; free, offline, no API key to protect; todo.md's "never expose the key" satisfied by design |
| 2026-08-24 | OLLAMA_HOST=0.0.0.0 on Windows + gateway-IP auto-probe in model/llm.py | WSL NAT can't reach Windows' loopback; auto-detection survives changing NAT subnets across reboots |
| 2026-08-24 | LLM answers only from RAG-retrieved documents (prompt-locked, sources echoed in API) | recommend.py/dataset stay the source of truth; LLM explains instead of inventing models or prices |
| 2026-08-24 | NDJSON streaming endpoint alongside plain JSON /ask-ai | CPU inference takes seconds; streaming keeps the chat UI responsive; retrieval validated before stream starts so HTTP errors still work |
| 2026-08-23 | SQLite over CSV for interaction logs | Concurrent-safe writes from FastAPI threadpool; queryable later for ML training |
| 2026-08-23 | Click logging centralised in App handlers | One hook covers both card buttons and the detail-modal compare path; rank comes from `_rank` stamped at search time |
| 2026-08-23 | Logging endpoints separate from /recommend | Analytics failures must never break recommendations; frontend `.catch(() => null)` mirrors this |
| 2026-08-23 | RAG before LLM (todo order kept) | Retrieval grounds every later LLM answer in real dataset rows; hallucinated prices/models become structurally impossible |
| 2026-08-23 | TF-IDF embeddings stored directly in ChromaDB | Deterministic, offline, zero model downloads, sklearn already a dependency; build <2s for 5,284 docs and ~11ms queries; swap point for MiniLM/BGE documented in rag.py |
| 2026-08-23 | Full laptop records live in collection metadata | /ask answers are grounded without re-reading the CSV; the future LLM can quote stored fields verbatim |
| 2026-08-23 | Budget phrases parsed out of the query text ("under 80k") | Keeps free-text /ask useful before any LLM exists; explicit max_price param always overrides |
| 2026-08-23 | fastapi.Query() instead of pydantic Field() for GET params | fastapi 0.141.1 + pydantic 2.13.4 reject pydantic-Field defaults on query params at route registration |
| 2026-09-08 | Floating scroll-to-top button + footer "Ask AI live" copy | Navigation ease (no way back up after long scroll); footer referenced Ask AI as "coming soon" when it shipped in Step 17 |

---

## Notes
- Dataset: 5,284 rows after cleaning (removed 35 duplicates, dropped IPS_Panel/Warranty/Price)
- Purpose column has 60 unique comma-separated multi-label values (parsed at runtime)
- Prices range from NPR 6,499 to NPR 1,130,809
- Brands: 27 total (HP, Lenovo, ASUS, Dell, MSI, Acer, Apple, Samsung, etc.)
- CPU/GPU tier scoring done at runtime via keyword matching in model/recommend.py
- Missing values (Storage_GB 40%, Touchscreen 43%, Weight_KG 36%) handled with defaults (0/Unknown) in the engine — works well enough for recommendations

---

## Project File Structure

```
garima/
├── instruct.md                        # Project requirements
├── LOGBOOK.md                         # This file
├── requirements.txt                   # Python dependencies
├── run.sh                             # Start API + UI servers
├── todo.md                            # Resumable task list / roadmap
├── data/
│   ├── laptops_ml_ready.csv           # Dataset (5,284 rows, 16 cols)
│   ├── interactions.db                # Click/search logs (Step 15)
│   └── chroma/                        # RAG vector index (Step 16; rebuild: python3 -m model.rag)
│       ├── chroma.sqlite3
│       ├── vectorizer.pkl             # Fitted TF-IDF vectorizer for query embedding
│       └── index_meta.json            # Build stats (count/dim/built_at)
├── model/
│   ├── __init__.py
│   ├── recommend.py                   # ML recommendation engine
│   └── rag.py                         # ChromaDB retrieval (/ask) — build_index() + ask()
├── api/
│   ├── __init__.py
│   ├── main.py                        # FastAPI server
│   └── interactions.py                # SQLite click/search logging
├── tests/
│   ├── __init__.py
│   ├── test_recommend.py              # 99 unit tests (engine + insights)
│   ├── test_api.py                    # API integration tests (incl. logging endpoints)
│   ├── test_e2e.py                    # End-to-end pipeline tests
│   └── test_rag.py                    # RAG unit + /ask integration tests
├── ui/
│   ├── app.py                         # Streamlit UI (legacy, still works)
│   └── static/
│       └── style.css                  # External CSS
├── frontend/                          # React + Vite app (primary UI)
│   ├── index.html                     # Entry page
│   ├── package.json                   # React 19, Vite 8
│   ├── vite.config.js                 # Dev proxy /api → :8000
│   ├── public/
│   │   └── favicon.svg                # Custom gradient laptop icon
│   └── src/
│       ├── main.jsx                   # React bootstrap
│       ├── App.jsx                    # Page composition + results state
│       ├── styles/index.css           # Design tokens & global styles
│       ├── data/options.js            # UI options mirroring backend enums
│       ├── services/api.js            # FastAPI client wrappers
│       └── components/                # Navbar, Hero, PurposeGrid,
│                                      # BudgetSelector, PreferencesPanel,
│                                      # FinderSection, ResultsSection,
│                                      # LaptopVisual, LaptopDetail,
│                                      # CompareTray, CompareModal,
│                                      # InsightsSection, ScrollToTop,
│                                      # Footer
└── visualization/
    ├── charts.py                      # Chart generation script
    └── charts/
        ├── 01_price_distribution.png
        ├── 02_brand_market_share.png
        ├── 03_price_by_brand.png
        ├── 04_purpose_distribution.png
        ├── 05_ram_vs_price.png
        ├── 06_cpu_gpu_tiers.png
        ├── 07_correlation_heatmap.png
        └── 08_storage_vs_price.png
```

---

## Installed Dependencies

```bash
python3 -m pip install --user --break-system-packages pandas numpy scikit-learn fastapi uvicorn matplotlib seaborn streamlit httpx pytest chromadb
```

See also: `requirements.txt` for version-pinned dependencies.

---

## Run Commands

| Service | Command | URL |
|---------|---------|-----|
| API | `python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000` | http://localhost:8000/docs |
| **React frontend** | `cd frontend && npm run dev` | http://localhost:5173 |
| Frontend prod build | `cd frontend && npm run build` (output in `frontend/dist`) | — |
| Streamlit UI (legacy) | `streamlit run ui/app.py --server.port 8501` | http://localhost:8501 |
| Charts | `python3 visualization/charts.py` | Saves to `visualization/charts/` |
| RAG index build | `python3 -m model.rag` | Creates `data/chroma/` (run once / after dataset changes) |
| ML Tests | `python3 model/recommend.py` | Console output |
| Unit Tests | `python3 -m pytest tests/test_recommend.py -v` | Console output |
| API Tests | `python3 -m pytest tests/test_api.py -v` | Console output |
| E2E Tests | `python3 -m pytest tests/test_e2e.py -v` | Console output |
| All Tests | `python3 -m pytest tests/ -v` | Console output |

---

## Remaining Work

### All Tasks Completed
- [x] Unit tests for recommendation logic (`model/recommend.py`)
- [x] API integration tests (test all endpoints with edge cases)
- [x] End-to-end test (UI -> API -> Model -> Response)
- [x] Test with malformed inputs (bad budget, empty purpose, etc.)
- [x] Performance check (response time for 5,284 dataset)
- [x] Add `requirements.txt` for reproducible installs
- [x] Add error handling in UI for edge cases
- [x] UI redesign following design.md (card-based, guided flow, accessible theme)
- [x] Optional spec filters (OS, CPU tier, GPU tier, Dedicated GPU)
- [x] Smart spec display (no more "N/A" — shows known specs)
- [x] React frontend: homepage, finder flow, live recommendations (21.md Phases 1–3)

### Next Up — 21.md Phases 4 & 5
- [x] Product details page/component (full specs, why recommended, Ask AI placeholder)
- [x] Comparison interface (select up to 4 laptops, side-by-side spec table)
- [x] Wire View Details / Compare buttons on result cards

### Optional Future Improvements
- [ ] Add `README.md` with project description and setup instructions
- [ ] Consider adding a CLI interface for terminal-only usage
- [ ] Consider Docker setup for deployment
