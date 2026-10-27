# How the System Works — Step by Step

## 1. Recommendation Engine (recommend.py / recommend_phones.py)

Not ML — hand-tuned weighted scoring. No training, no model, just math.

### Laptop Scoring Formula

```
Final Score = Budget (35%) + Purpose (25%) + Specs avg (35%) + Balance (5%)
```

**Budget fit (35%) — recommend.py:311-337**

- Price within 60-100% of budget → 100 pts (great value)
- Price within 30-60% → 80 pts (good but might be lower spec)
- Price over budget by ≤15% → 50-30 pts (close enough)
- Price over by >30% → penalty

**Purpose match (25%) — recommend.py:339-353**

- User types "gaming" → PURPOSE_KEYWORD_MAP maps it to ["Gaming"]
- Checks overlap with laptop's purpose labels from the CSV
- overlap / total_purposes * 100 = score

**Specs average (35%) — recommend.py:355-430**

- RAM, storage, CPU tier, GPU tier, brand — each scored 0-100
- Averaged together
- CPU/GPU tiers come from giant lookup tables (CPU_TIERS at line 43, GPU_TIERS at line 139)
- Tiers match model name strings to tiers 1-6

**Balance bonus (5%) — recommend.py:432-435**

- If CPU tier and GPU tier are close → bonus (balanced machine)
- If CPU is tier 6 but GPU is tier 1 → penalty (bottleneck)

### Hard Filters Before Scoring (recommend.py:554-571)

- Price > 1.5x budget → skip
- RAM < 50% of requested → skip
- Wrong storage type → skip
- Screen too small → skip
- No touchscreen when requested → skip
- Integrated GPU when dedicated requested → skip

### Deal Detection (recommend.py:463-527)

Groups laptops by (cpu_tier, gpu_tier, ram_band), finds median price in each group:

- Price ≤ 85% of median → "Great deal"
- Price ≤ 97% → "Good value"
- Price > 110% → "Premium"

### Phone Scoring (recommend_phones.py:168-311)

Same idea but different weights:

```
Budget (30%) + Purpose (20%) + Chipset (20%) + Camera (10%) + Battery (10%) + Connectivity (10%)
```

- Camera scored by MP tiers (108MP=95, 64MP=80, etc.) + OIS bonus
- Battery scored by mAh tiers + fast charging wattage bonus
- Connectivity = 5G (40pts) + NFC (30pts) + fingerprint (30pts)

---

## 2. RAG System (rag.py / rag_phones.py)

RAG = Retrieval-Augmented Generation. Used for the AI chatbot, not the main recommendation.

### The Problem It Solves

The LLM (Mistral) doesn't know your dataset. If you ask "what's a good gaming laptop under 100k", it might hallucinate models/prices. RAG forces it to only describe real laptops from your CSV.

### Step 1: Build Documents (rag.py:117-146)

Each laptop row becomes a natural-language paragraph:

```
"ASUS Intel laptop. Core i7-13700H processor (high-performance CPU,
tier 5 of 6). NVIDIA GeForce RTX 4060 dedicated NVIDIA graphics
suitable for gaming, tier 5 of 6. 16GB RAM. 512GB SSD storage.
15.6 inch display. runs Windows 11. weighs 2.2kg (standard weight).
priced at NPR 145,000 (premium high-end expensive). suited for Gaming,
Video Editing."
```

This text is what gets vectorized. The semantic meaning ("gaming", "cheap", "lightweight") is what makes search work.

### Step 2: TF-IDF Vectorization (rag.py:173-178)

```python
vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), sublinear_tf=True)
embeddings = vectorizer.fit_transform(documents).toarray()
```

**What TF-IDF does:**

- **TF** (Term Frequency): How often does word "gaming" appear in this document? More = higher weight.
- **IDF** (Inverse Document Frequency): How rare is "gaming" across ALL 5,284 documents? Rare words get higher weight. Common words like "laptop" get lower weight.
- **Result**: Each document becomes a 4000-dimensional vector where numbers represent how "important" each word/ngram is to that document.

**ngram_range=(1,2)** means it considers both single words ("gaming") and pairs ("gaming laptop", "RTX 4060").

**sublinear_tf=True** means it uses 1 + log(tf) instead of raw frequency, so a word appearing 10 times isn't 10x more important — just a bit more.

### Step 3: Store in ChromaDB (rag.py:180-195)

```python
collection = client.create_collection(name="laptops", metadata={"hnsw:space": "cosine"})
collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
```

ChromaDB stores:

- The vectors (for similarity search)
- The original text documents (for context)
- The full laptop metadata (for grounded answers)
- Builds an HNSW index (approximate nearest neighbor graph) for fast cosine similarity search

The fitted vectorizer is pickled and saved separately — it must be reused at query time so the vocabulary mapping stays consistent.

### Step 4: Query (rag.py:277-332)

User asks: "lightweight gaming laptop under 100k"

1. `extract_budget_hint("under 100k")` → 100000 (regex extracts the number)
2. `vectorizer.transform(["lightweight gaming laptop under 100k"])` → converts query to same 4000-dim vector space
3. `collection.query(query_embeddings=[...], n_results=5, where={"price_npr": {"$lte": 100000}})` → ChromaDB finds 5 most cosine-similar laptops, filtered to ≤100k
4. Returns the laptop records + their spec-sheet documents

### Step 5: LLM Generates Answer (llm.py)

The retrieved laptops are injected into the Mistral prompt as context:

```
You are a helpful assistant. Answer using ONLY the laptops below:

1. ASUS TUF Gaming F15 - i5-12500H, RTX 4050, 16GB RAM, NPR 105,000
2. Lenovo IdeaPad Gaming 3 - Ryzen 5 7535HS, RTX 3050, 8GB RAM, NPR 75,000
...

User question: lightweight gaming laptop under 100k
```

The LLM can only describe what's in the context — it can't invent models.

---

## Summary

| System | What it does | How |
|---|---|---|
| **Recommendation** | Ranked list from structured filters | Weighted scoring (budget + purpose + specs), no vectors |
| **RAG** | Free-text semantic search over dataset | TF-IDF vectors → ChromaDB cosine similarity |
| **TF-IDF** | Convert text to numbers | Counts word importance (rare = high weight, common = low) |
| **ChromaDB** | Store vectors + fast similarity search | HNSW graph index, cosine distance |
| **LLM** | Generate natural language answer | Takes RAG results as context, can only cite real data |
