# Project Information

## LaptopFinder Nepal — AI Laptop Recommendation System

---

### Members

| Name | Student ID | Section |
|------|------------|---------|
| Garima Dangol | `[Student ID]` | `[Section]` |
| `[Member name]` | `[Student ID]` | `[Section]` |

---

## Executive Summary

LaptopFinder Nepal is an end-to-end, AI-powered laptop shopping assistant that recommends laptops from a curated dataset of **5,284 real laptops priced in Nepali Rupees (NPR)**. Users describe what they need — budget and purpose are required (e.g., gaming, programming, video editing, student use), while specs like RAM, storage, brand, CPU/GPU tier, touchscreen or dedicated GPU are optional — and the system returns a **ranked list of matching laptops with prices, full specifications, and a plain-language explanation of why each one was recommended**. If nothing matches exactly, it falls back to the closest suitable alternatives instead of returning empty results.

The core is a **content-based machine-learning recommendation engine**: every laptop's processor and graphics card are graded on an engineered 6-tier power scale, purposes are parsed from free text into canonical labels (including multi-purpose combinations like "Gaming and Programming"), and candidates are scored on a weighted blend of budget fit (35%), purpose match (25%), specification strength (35%), and overall balance (5%). Retrieval is augmented by a **RAG layer** — all 5,284 laptops are indexed as natural-language spec sheets in a local ChromaDB vector database, enabling free-text Q&A ("lightweight student laptop under 50k") with automatic budget-phrase extraction.

On top of retrieval sits an **"Ask AI" chatbot powered by a locally-hosted Mistral LLM via Ollama** — no cloud APIs, no keys, fully offline. The LLM is structurally prevented from hallucinating: it may only explain laptops returned by the dataset-grounded retriever and must cite exact models and NPR prices. The web experience is a modern React e-commerce interface with a guided three-step finder flow, loading skeletons, product detail modals, side-by-side comparison with best-value highlighting, interactive market-insight dashboards built from the dataset, and per-brand illustrated product cards. Every search and click is logged to SQLite, laying the groundwork for future collaborative-filtering models trained on real user behaviour. The entire pipeline is verified by a suite of **206 automated tests** spanning unit, API integration, and end-to-end layers.

---

## Technologies / Tools Used

| Layer | Technology |
|-------|-----------|
| Language | Python 3, JavaScript (ES6+) |
| Machine Learning | scikit-learn (TF-IDF vectorization, feature engineering), custom content-based scoring & ranking engine |
| RAG / Vector Search | ChromaDB (persistent cosine-space vector index), TF-IDF embeddings |
| Generative AI | Ollama (Mistral LLM, locally hosted — streaming chat API, grounded prompting) |
| Data Processing | pandas, NumPy |
| Backend API | FastAPI (10+ REST endpoints, Pydantic validation, CORS, NDJSON streaming responses), Uvicorn |
| Database / Storage | CSV dataset, SQLite (interaction/click logging), ChromaDB persistence |
| Data Visualization | Matplotlib & Seaborn (static report charts), Recharts (live in-app dashboards) |
| Frontend | React 19 + Vite, custom CSS design system (responsive, accessible, reduced-motion safe) |
| Legacy UI | Streamlit prototype (kept functional) |
| Testing | pytest — 206 tests (unit + API integration + end-to-end), oxlint, production builds |
| Tools & Environment | Git-friendly project layout, WSL2 + Windows (cross-platform dev), Node.js/npm, curl smoke testing |

---

## Unique Selling Point (USP)

> **A hallucination-proof, 100% local AI shopping assistant for the Nepali laptop market.**

Three things no typical "AI recommender" offers together:

1. **Grounded AI that cannot lie about products.** Most LLM chatbots invent laptops, prices, and specs. Our Ask-AI bot is *structurally* grounded: the Mistral model never sees the open internet — only spec sheets retrieved from our own verified dataset, and every answer ships back with its cited source laptops. Prices and models in AI answers are always real dataset values, by construction, not by prompt-hoping.

2. **Free, private, and offline-capable.** The entire intelligence stack — recommendations, vector search, and the LLM itself — runs on the user's own hardware via Ollama. No API keys, no subscription fees, no user data leaving the machine: genuinely deployable in bandwidth-limited and cost-sensitive contexts like Nepal.

3. **Explainable, shopper-first recommendations.** Instead of a black-box score, every result carries human-readable reasons ("RTX 4060 fits your gaming purpose") and honest trade-offs ("slightly over budget"), plus side-by-side comparison with automatic best-value highlighting — closer to a knowledgeable shop assistant than a search filter.
