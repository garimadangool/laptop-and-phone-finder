# LaptopFinder Nepal — Deep Technical Walkthrough

**Project:** AI-Powered Laptop Recommendation System
**Dataset:** 5,284 real laptops with NPR pricing (Nepali Rupees)
**Team:** Garima Dangol

---

## 1. System Architecture — How the Pieces Connect

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                           │
│  React 19 Frontend — localhost:5173                              │
│  Finder → Results → Detail Modal → Ask AI Chat                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP (Vite proxy → /api → FastAPI)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend :8000                         │
│  POST /recommend  │  GET /ask  │  POST /ask-ai  │  /log-*      │
└──────┬────────────┴─────┬──────┴──────┬─────────┴──────────────┘
       │                  │             │
       ▼                  ▼             ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  recommend.py│  │   rag.py     │  │  llm.py           │
│  (ML Engine) │  │ (Vector DB)  │  │ (Ollama/Mistral)  │
└──────────────┘  └──────────────┘  └──────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
   CSV Dataset      ChromaDB Index     Local Mistral LLM
   (5,284 rows)     (TF-IDF vectors)   (runs on Windows)
```

The user never talks to any of these directly. They interact with a React frontend
that sends HTTP requests to a FastAPI server. The server delegates to three Python
modules depending on what the user asked for.

---

## 2. The Dataset

**File:** `data/laptops_ml_ready.csv` — 5,284 laptops, 16 columns.

Each row is a real laptop sold in Nepal with these fields:

| Field | Example | Why it matters |
|-------|---------|---------------|
| `Brand` | ASUS, HP, Dell, MSI, Apple... (27 brands) | Used for brand preference filtering |
| `CPU_Model` | "Core i7-13700H" | Graded into CPU tier 1-6 |
| `CPU_Brand` | Intel / AMD / Apple | Display & grouping |
| `GPU_Model` | "GeForce RTX 4060" | Graded into GPU tier 1-6 |
| `GPU_Brand` | NVIDIA / AMD / Intel | Display & grouping |
| `RAM_GB` | 8, 16, 32, 64 | Spec matching |
| `Storage_GB` | 256, 512, 1000 | Spec matching |
| `Storage_Type` | SSD / HDD / Flash | Filter preference |
| `Screen_Size_Inches` | 15.6, 14, 16 | Min screen filter |
| `Touchscreen` | 0 or 1 | Optional filter |
| `Weight_KG` | 1.5, 2.1 | Used in RAG document text |
| `Operating_System` | Windows 11, macOS, Linux | OS preference |
| `Price_NPR` | 89,999 | Budget matching |
| `Purpose` | "Gaming, Student" | Matched to user's stated purpose |

**Preprocessing happens at runtime** (`model/recommend.py:preprocess()`):
- Missing `Storage_GB` → defaults to `0.0`
- Missing `Storage_Type` → defaults to `"Unknown"`
- Missing `GPU_Model` → defaults to `"Integrated"`
- Missing `OS` → defaults to `"Unknown"`
- The `Purpose` string is split on commas into a list of labels

---

## 3. The ML Recommendation Engine

**File:** `model/recommend.py` — this is the core. No cloud, no API, pure Python scoring.

### 3.1 Purpose Parsing (Free Text → Canonical Labels)

The user types something like `"video editing and graphic design"`. The engine
keyword-scans it against a dictionary:

```python
PURPOSE_KEYWORD_MAP = {
    "gaming": ["Gaming"],
    "programming": ["Programming"],
    "video editing": ["Video Editing", "Graphic Design"],
    "student": ["Student", "General Use"],
    "ai": ["AI / Machine Learning"],
    "machine learning": ["AI / Machine Learning"],
    "data science": ["AI / Machine Learning", "Heavy Multitasking"],
    # ... 15 keyword entries total
}
```

Result: `"video editing and graphic design"` → `{Video Editing, Graphic Design}`

The frontend joins multiple purpose selections with `" and "` (e.g., `"Gaming and Programming"`), so the keyword scanner matches both. Each laptop in the dataset also has purpose labels, and overlap is scored.

### 3.2 Budget Parsing (Flexible Formats → Number)

The engine parses budget strings that users naturally type:

| Input | Parsed as |
|-------|-----------|
| `"100000"` | 100,000 NPR |
| `"1.5 lakh"` | 150,000 NPR |
| `"80k"` | 80,000 NPR |
| `"50,000"` | 50,000 NPR |
| `"3 lakh"` | 300,000 NPR |

Logic: extract the number → check for `lakh/lac` (×100,000) or `k` (×1,000). If the number is under 1,000 and no unit, it is assumed to be in thousands (e.g., `"60"` → 60,000).

### 3.3 CPU Tier System (1-6 Scale)

Every CPU model string is matched against a hand-curated dictionary of ~150 patterns
grouped into 6 tiers:

| Tier | Examples | Meaning |
|------|----------|---------|
| 1 | Celeron, Pentium, Athlon, Atom, Snapdragon 7c | Entry-level, basic tasks |
| 2 | Core i3, Ryzen 3 | Basic mainstream |
| 3 | Core i5 (10th-12th gen), Ryzen 5 (older gen) | Solid mid-range |
| 4 | Core i7 (older gen), Ryzen 7 (5000-7000 series) | Fast performance |
| 5 | Core i7 (13th-14th gen), Core Ultra 7/9, Ryzen 9 | High-performance |
| 6 | Core i9 (12th+ gen), Apple M1-M5, Ryzen AI Max | Workstation flagship |

The matching works by checking if any pattern string is a substring of the CPU model name (lowercased). The **highest matching tier wins** — so a Ryzen 7 7840HS matches tier 4 patterns AND tier 5 patterns, and tier 5 wins.

### 3.4 GPU Tier System (1-6 Scale)

Same approach, ~100 patterns:

| Tier | Examples | Meaning |
|------|----------|---------|
| 1 | Radeon R2-R5, UHD 600, HD 500 | Integrated/entry graphics |
| 2 | UHD 620, Iris Xe (80EU), GeForce MX series, Radeon 780M | Light dedicated / strong integrated |
| 3 | GTX 1050, RTX 3050, Iris Xe (96EU), Arc A350M | Entry gaming |
| 4 | RTX 4050, GTX 1660 Ti, RTX 3050 6GB | Mid gaming |
| 5 | RTX 3060-3080, RTX 4060-4070, RTX 5060-5070 | High-end gaming |
| 6 | RTX 4080-4090, RTX 5080-5090, Apple M-series, Radeon RX 7900 | Flagship |

### 3.5 The Scoring Formula

This is the core math. For every laptop in the dataset that passes the initial filters,
the engine calculates a **score from 0 to 100** using four weighted components:

```
Final Score = Budget Score × 0.35
            + Purpose Score × 0.25
            + Specs Score × 0.35
            + Balance Score × 0.05
```

#### Budget Score (35% weight)

```
If laptop price ≤ user budget:
    ratio = price / budget
    if ratio ≥ 0.6  → score = 100 (great value, uses budget well)
    if ratio ≥ 0.3  → score = 80 + (ratio - 0.3) × 66.7
    else            → score = 40 + ratio × 133.3 (very cheap, might be low spec)

If laptop price > user budget:
    over = (price - budget) / budget
    if over ≤ 15%  → score = 50 - over × 200  (close enough)
    if over ≤ 30%  → score = 20 - over × 50   (slightly over)
    else           → score = max(0, 10 - over × 20)  (significantly over, penalized)
```

**Why 35%?** Budget is the strongest constraint for Nepali buyers — most shoppers have
a hard ceiling. This weight ensures the system respects it while still surfacing
near-budget options if nothing matches exactly.

#### Purpose Score (25% weight)

```
overlap = user_purpose_labels ∩ laptop_purpose_labels
if overlap exists:
    score = (number of overlapping labels / total user labels) × 100, capped at 100
else:
    score = 20 (penalty — purpose doesn't match)
```

Example: User wants `{Gaming, Programming}`. Laptop has `{Gaming, Student}`.
Overlap = `{Gaming}` → score = (1/2) × 100 = 50.

**Why 25%?** Purpose matters but shouldn't override a great spec deal — a powerful
laptop at a good price is useful even if its "primary purpose" label doesn't perfectly
align.

#### Specs Score (35% weight)

This is an average of up to 6 sub-scores (one per spec the user specified):

**RAM sub-score:**
```
If user specified min_ram:
    if laptop RAM ≥ requirement → score = min(100, (actual/min) × 50 + 50)
    else → score = (actual/min) × 50  (partial credit)
If no RAM specified:
    16GB+ → 80, 8GB+ → 50, under 8GB → 25
```

**Storage sub-score:** Same formula, defaults to 50 if present, 20 if missing.

**CPU tier sub-score:**
```
If user specified min_cpu_tier:
    if laptop tier ≥ requirement → score = min(100, 50 + (tier - requirement + 1) × 10)
    else → score = (laptop_tier / required_tier) × 50
If no tier specified: score = (laptop_tier / 6) × 100
```

**GPU tier sub-score:** Same formula as CPU.

**Brand sub-score:**
```
If user specified a brand:
    match → 100
    no match → 10 (heavy penalty)
```

All sub-scores are averaged, then weighted at 35%.

**Why 35%?** Specs are what make a laptop actually do the job. A gaming laptop needs
a good GPU regardless of budget or purpose labels.

#### Balance Score (5% weight)

```
balance = 100 - abs(cpu_tier - gpu_tier) × 15
score = max(0, balance)
```

This rewards laptops where CPU and GPU tiers are similar. A laptop with CPU tier 5 and
GPU tier 5 scores 100 here. One with CPU tier 5 and GPU tier 2 scores 55 — it's
unbalanced. This prevents recommending a workstation CPU paired with weak graphics
for a gaming query.

### 3.6 Filtering (Before Scoring)

Before scoring, the engine filters out laptops that are clearly wrong:

| Filter | Rule |
|--------|------|
| Budget ceiling | Price > 1.5 × budget → removed |
| Minimum RAM | Laptop RAM < 50% of requested → removed |
| Storage type | If user wants SSD, HDD-only laptops removed |
| Minimum screen | Screen < requested minimum → removed |
| Touchscreen | If required, non-touch laptops removed |
| Dedicated GPU | If required, integrated-only laptops removed |

### 3.7 Fallback (No Exact Match)

If zero laptops pass filters, the engine falls back to the **5 cheapest laptops** (if budget exists) or the **5 cheapest overall**. These are scored normally but each gets an extra reason: "Closest alternative (no exact match found)".

### 3.8 Deal Detection

After scoring, each laptop is compared to **other laptops with the same CPU tier, GPU tier, and RAM band** (8GB/16GB/32GB+):

```
median_price = median price of comparable laptops
ratio = laptop_price / median_price

if ratio ≤ 0.85 → "great deal" (15%+ cheaper than comparable)
if ratio ≤ 0.97 → "good deal" (competitive pricing)
if ratio ≤ 1.10 → "fair" (normal pricing)
else            → "premium" (overpriced for its specs)
```

This is how the "🏷️ Deals only" filter works on the frontend.

---

## 4. RAG (Retrieval-Augmented Generation)

**File:** `model/rag.py`

### 4.1 What RAG Does

RAG lets users ask **natural language questions** like "lightweight gaming laptop under 50k" and get back real laptops from our dataset. Without RAG, the user would have to manually set every filter. RAG understands intent.

### 4.2 Index Building (One-Time)

```
Step 1: Load all 5,284 laptops from CSV
Step 2: For each laptop, generate a natural-language "spec sheet" document:
    "ASUS Intel laptop. Core i7-13700H processor (fast performance CPU, tier 4 of 6).
     GeForce RTX 4060 dedicated NVIDIA graphics suitable for gaming, tier 5 of 6.
     16GB RAM. 512GB SSD storage. 15.6 inch display. runs Windows 11.
     weighs 2.1kg (standard weight). priced at NPR 129,999 (premium high-end expensive).
     suited for Gaming, Programming."

Step 3: Convert all documents to TF-IDF vectors (4,000 features, 1-2 gram range)
Step 4: Store vectors + documents + metadata in ChromaDB (cosine similarity space)
Step 5: Save the fitted vectorizer (pickle) so queries use the same vocabulary
```

### 4.3 Query Processing

When the user asks "gaming laptop with RTX graphics under 100k":

```
Step 1: Extract budget hint via regex
    "under 100k" → max_price = 100,000

Step 2: Transform query text using the SAME fitted vectorizer
    query_vector = vectorizer.transform(["gaming laptop with RTX graphics under 100k"])

Step 3: Query ChromaDB for top-N nearest vectors (cosine distance)
    WHERE price_npr ≤ 100,000  (applied as a metadata filter)
    Returns: 5 most similar laptops + their stored documents + distance scores

Step 4: Convert distance to similarity: similarity = max(0, 1 - distance)
```

### 4.4 Why TF-IDF Instead of a Neural Embedding Model?

- **No download required** — works offline, no model weights to ship
- **Deterministic** — same input always gives same output
- **Fast** — vectorization is a matrix multiply, no GPU needed
- **Good enough** — laptop spec text is technical/domain-specific where TF-IDF keyword matching actually works well (the words "RTX 4060" or "gaming" are strong signals)

The system is designed so you can swap in a neural model (like MiniLM or BGE) later
without changing the interface.

---

## 5. The LLM "Ask AI" Chatbot

**File:** `model/llm.py`

### 5.1 Why an LLM?

The recommendation engine returns structured data (scores, reasons, penalties). But
users often want to ask follow-up questions like:
- "Is this good value for the price?"
- "How does it handle modern games?"
- "Any downsides I should know?"

An LLM can answer these in natural language — but only if it's **grounded** so it doesn't hallucinate fake laptops or prices.

### 5.2 How Grounding Works (The Anti-Hallucination System)

The pipeline for every question:

```
User question
    ↓
RAG retrieval (model/rag.py) → finds 5 real laptops from dataset
    ↓
Build a "context block" for the LLM:
    "Other relevant laptops from our dataset (most relevant first):
     [1] ASUS Intel laptop. Core i7-13700H... priced at NPR 129,999...
     [2] HP AMD laptop. Ryzen 7 7840HS... priced at NPR 94,990...
     ..."
    ↓
Send to Ollama/Mistral with a strict system prompt:
    "Answer ONLY using the laptop data provided.
     Cite exact brand names, model names and NPR prices.
     Never invent laptops, specs, prices, stock or warranty information.
     Be concise, under 120 words."
    ↓
LLM generates an answer that can ONLY reference the retrieved laptops
```

The LLM never sees the internet. It never sees the full dataset. It only sees the
5 laptops RAG retrieved. So every brand name, model number, and price in its answer
comes from our verified dataset — by construction, not by prompt-hoping.

### 5.3 Focus Context

When the user opens the "Ask AI" panel from a specific laptop's detail modal, that
laptop's full spec line is injected into the prompt:

```
"The user is currently viewing this laptop:
 ASUS Intel Core i7-13700H, NVIDIA GeForce RTX 4060, 16GB RAM, 512GB SSD,
 15.6 inch, NPR 129,999, suited for Gaming, Programming"
```

This lets follow-up questions like "is this one good value?" or "what about its battery?" be understood correctly — the LLM knows which laptop the user is asking about.

### 5.4 Conversation History

The chatbot keeps the last 6 turns (3 user + 3 assistant). History is sent with each request so multi-turn conversations work:

```
User: "Is this good value?"
Assistant: "At NPR 129,999 for an RTX 4060 + i7-13700H, it's competitive..."
User: "What about the cheaper one?"
Assistant: "The HP at NPR 94,990 with RTX 4050 is better value per rupee..."
```

### 5.5 Streaming

The `/ask-ai/stream` endpoint uses NDJSON (newline-delimited JSON) so the UI can show text as it's generated:

```
{"type":"start","model":"mistral","sources":[...]}
{"type":"delta","text":"At"}
{"type":"delta","text":" NPR"}
{"type":"delta","text":" 129"}
...
{"type":"done","answer":"At NPR 129,999...","elapsed_ms":6100}
```

The React frontend reads these events in real-time and appends each chunk to the chat bubble — so the user sees the answer being typed out word by word.

### 5.6 Local Ollama Setup

The LLM runs entirely on the user's machine via Ollama (no cloud API keys):
- Default model: Mistral (7B parameters)
- Runs on the Windows host; the WSL-based API connects via the NAT gateway IP
- Auto-detects the Ollama server by probing multiple candidate URLs on each request
- First query after idle takes ~8 seconds (loading model into RAM); subsequent queries are ~3-6 seconds

---

## 6. The React Frontend

**Directory:** `frontend/` — React 19 + Vite + custom CSS design system

### 6.1 The Three-Step Finder Flow

The user experience is designed as a guided shopping assistant, not a form:

**Step 1 — Purpose Selection:**
- 10 category cards with icons (Gaming, Programming, Student, Creative Work, Office, Everyday Use, AI/ML, etc.)
- Multi-select: user can pick "Gaming + Programming" together
- Selected labels are joined with " and " and sent to the backend

**Step 2 — Budget Input:**
- Slider from 25,000 to 300,000+ NPR
- Quick-pick chips: 30K, 50K, 80K, 1 Lakh, 1.5 Lakh, 2 Lakh+
- Price formatted in Nepali style (en-IN locale)

**Step 3 — Optional Preferences:**
- Expandable panel with chip groups for: RAM, Storage, Brand (live from API), CPU/GPU tier, Screen size, Touchscreen, Dedicated GPU
- All optional — skip if you don't have specific requirements

### 6.2 How a Search Flows Through the System

```
1. User clicks "Find My Laptop →"
2. FinderSection.jsx builds the payload:
   {
     budget: "100000",
     purpose: "Gaming and Programming",
     min_ram: 16,
     ...
     top_n: 12
   }
3. beginSearch() generates a unique session ID (crypto.randomUUID)
4. POST /recommend → FastAPI → recommend() → scored + ranked results
5. logSearch() fires a background POST to /log-search (fire-and-forget)
6. Results passed to ResultsSection → rendered as product cards
7. syncUrl() writes filters to the URL bar (shareable/bookmarkable link)
8. Browser scrolls to results section
```

### 6.3 Result Cards

Each laptop is displayed as a product card with:
- **Laptop visual:** SVG illustration colored by brand (26 brand themes)
- **Score pill:** Match percentage (e.g., "92% match") in green
- **Deal badge:** "🏷️ Great deal" / "Good deal" / "Premium" if applicable
- **Price:** NPR formatted (e.g., "NPR 94,990") in bold
- **Spec pills:** RAM, Storage, GPU, CPU, OS, Screen size
- **Reasons:** Green tags like "Matches your purpose: Gaming"
- **Penalties:** Orange tags like "15% over budget"
- **Buttons:** "View Details" (opens modal) + "♡ Save" (favorites)
- **"Best Match"** gradient badge on the #1 result

### 6.4 Sorting and Filtering

A toolbar above results provides:
- **Sort chips:** Best match (ranked), Price low→high, Price high→low, RAM↑, Storage↑
- **Deals only toggle:** Filters to only "great deal" laptops, shows count
- **Results counter:** "X laptops"
- **Show more:** Initially shows 6 cards, "Show more laptops (N more) ↓" button reveals 6 more per click (up to 12 total fetched)

### 6.5 Product Detail Modal

Clicking "View Details" opens a full modal with:
- Brand badge, laptop name, price, score
- Full specification table (CPU/GPU + tiers, RAM, storage, display, OS, weight, suited-for)
- "Why it was recommended" section (reasons from the engine)
- "Things to consider" section (penalties from the engine)
- **Compare button** — adds to the comparison tray (max 4 laptops)
- **Ask AI button** — opens the chatbot panel for this specific laptop

### 6.6 Side-by-Side Comparison

- **CompareTray:** Floating bottom bar appears when laptops are picked; shows selected chips, "Clear" button, "⇄ Compare (n)" button (enabled at 2+ selections, max 4)
- **CompareModal:** Side-by-side table comparing: Price, Match score, Processor, CPU tier, Graphics, GPU tier, Memory, Storage, Display, Weight, OS, Suited-for
- **Best-value highlighting:** ★ marks the winner per row (lowest price, highest score, best specs). Ties are intentionally not marked. A legend explains the star.
- **Mobile:** Horizontal scroll with edge shadows and drag-to-scroll support

### 6.7 Favorites (Saved Laptops)

**How it works:**

```javascript
// favorites.js — pure client-side, localStorage
const KEY = "laptopfinder.favorites.v1";

// Unique ID for a laptop: "brand|cpu_model|ram_gb|storage_gb|price_npr"
function favoriteId(rec) {
  return [laptop.brand, laptop.cpu_model, laptop.ram_gb,
          laptop.storage_gb, laptop.price_npr].join("|");
}

// Toggle saves/removes the full recommendation object
function toggleFavorite(rec) {
  const id = favoriteId(rec);
  const { laptop, score, deal, reasons, penalties } = rec;
  // Add to or remove from localStorage array
  // Returns the updated favorites array
}
```

- **Storage:** `localStorage` — survives page reloads and browser restarts
- **What's saved:** Full laptop object + score + deal info + reasons + penalties (so saved items can open fully in the detail modal later)
- **UI:** Heart icon on each result card + "Save" button in the detail modal
- **FavoritesSection:** Shows saved laptops in a grid with "View" / "Remove" / "Clear all" buttons
- **No server involvement** — everything is in the browser

### 6.8 Shareable Search URLs

After a search, the filters are written to the URL:

```
http://localhost:5173/?purpose=Gaming+Programming&budget=100000&ram=16
```

When someone opens this link:
1. `formFromUrl()` reads the query parameters and hydrates the form
2. Auto-runs the search once on mount
3. Recipient sees the exact same results

This means searches are bookmarkable and shareable without any backend support.

---

## 7. Interaction Logging (Future ML Training)

**File:** `api/interactions.py` — SQLite database at `data/interactions.db`

### 7.1 What Gets Logged

**Every search:**
```sql
search_events: timestamp, session_id, budget, purpose, filters,
               status, results_shown, top_score
```

**Every click:**
```sql
click_events: timestamp, session_id, action (view_details/compare_add/show_more),
              position_in_list, score, brand, cpu_model, gpu_model,
              ram_gb, storage_gb, price_npr
```

### 7.2 Why This Matters

This data is the foundation for **collaborative filtering** — a future ML model
that learns "users who looked at gaming laptops under 100K also tended to buy X".
The current system is content-based (specs only); interaction data would let it learn
from real user behavior.

The logging is **fire-and-forget** — it never blocks the UI or shows errors to the user. If the logging endpoint is down, the search/click still works fine.

---

## 8. The API Layer

**File:** `api/main.py` — FastAPI with Pydantic validation

### 8.1 All Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/` | API info + endpoint map |
| POST | `/recommend` | Ranked laptop recommendations (main ML engine) |
| GET | `/brands` | All 27 brands from the dataset |
| GET | `/purposes` | 10 canonical purpose labels |
| GET | `/stats` | Dataset statistics (counts, price range) |
| GET | `/insights` | Aggregated charts data (price histogram, brand distribution, RAM vs price, tier distributions) |
| GET | `/ask` | RAG free-text search (returns real laptops, no LLM) |
| POST | `/ask-ai` | RAG + LLM answer (one-shot JSON) |
| POST | `/ask-ai/stream` | RAG + LLM answer (NDJSON streaming) |
| POST | `/log-search` | Log a search event to SQLite |
| POST | `/log-click` | Log a click event to SQLite |
| GET | `/logs/stats` | Logging summary |

### 8.2 Request Validation

Every endpoint uses Pydantic models for validation. For example, the recommend endpoint:
```python
class RecommendRequest(BaseModel):
    budget: str          # Required — "100000", "1.5 lakh", "80k"
    purpose: str         # Required — "gaming", "video editing"
    min_ram: Optional[float] = None
    min_storage: Optional[float] = None
    brand: Optional[str] = None
    min_cpu_tier: Optional[int] = Field(None, ge=1, le=6)
    top_n: Optional[int] = Field(5, ge=1, le=20)
```

Invalid requests get automatic 422 error responses with clear messages.

---

## 9. Testing

**206 automated tests** across three layers:

| File | Tests | What they cover |
|------|-------|----------------|
| `tests/test_recommend.py` | 99 | Every function in the ML engine: tier scoring, budget parsing, purpose parsing, scoring logic, recommendations, deal detection, dataset stats |
| `tests/test_api.py` | 19 | API endpoint integration: correct responses, validation errors, edge cases |
| `tests/test_e2e.py` | 10 | Full pipeline: UI input → API → model → response |
| `tests/test_rag.py` | ~30 | RAG index building, querying, budget extraction, brand filtering |
| `tests/test_llm.py` | 34 | LLM prompt construction, host resolution, chat generation, streaming, endpoint integration |

All tests run with `python3 -m pytest tests/ -v` and complete in under 30 seconds.

---

## 10. Design System

### Color Palette
- **Background:** Warm off-white `#faf7f1`
- **Primary:** Deep blue `#2337b8` (buttons, headings, links)
- **Secondary:** Violet `#7c3aed` (badges, gradients)
- **Success:** Emerald `#059669` (prices, scores, positive tags)
- **Text:** Near-black `#191d35` (strong contrast)
- **Light theme only** — no dark mode

### Typography
- **Font:** Inter (headings) + system fallback
- **Minimum size:** 0.75rem (accessibility)

### Accessibility
- WCAG-compliant contrast ratios
- `aria-label`, `aria-pressed`, `aria-modal`, `role="dialog"` on interactive elements
- `prefers-reduced-motion` disables animations
- Information never conveyed by color alone (always has icons/labels/text)

---

## 11. How to Run Everything

```bash
# Terminal 1 — FastAPI backend
cd ~/garima
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — React frontend
cd ~/garima/frontend
npm run dev
# Opens at http://localhost:5173

# For Ask AI chatbot (optional):
# Ollama must be running on Windows with mistral pulled
# ollama serve  (or open Ollama desktop app)
```

The frontend automatically proxies API calls to the backend via Vite's dev server configuration.
