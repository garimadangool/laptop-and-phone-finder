"""RAG retrieval over the laptop dataset using ChromaDB.

Indexes every laptop as a natural-language "spec sheet" document plus its full
formatted record as metadata, so free-text questions ("lightweight gaming
laptop under 100k") retrieve real laptops from OUR dataset - never invented
ones. Retrieval is fully local and deterministic:

- Vector store : ChromaDB PersistentClient at data/chroma/ (cosine space)
- Embeddings   : scikit-learn TF-IDF vectors computed once at build time and
                 stored directly in Chroma (no model download needed; swap in
                 MiniLM/BGE later without changing this module's interface)

Build the index once with:   python3 -m model.rag
Ask through the API with:    GET /ask?query=gaming%20laptop%20under%20100k

Heavy imports (chromadb/sklearn/numpy) are done lazily inside functions so
importing this module stays cheap for the API and the test suite.
"""

import json
import os
import pickle
import re
from datetime import datetime

from model.recommend import load_data, preprocess, format_laptop, cpu_tier, gpu_tier

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "laptops_ml_ready.csv")
DEFAULT_INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")

COLLECTION_NAME = "laptops"
VECTORIZER_FILE = "vectorizer.pkl"
META_FILE = "index_meta.json"

# Index directory override used by the test suite (mirrors interactions.set_db_path).
INDEX_DIR = DEFAULT_INDEX_DIR

_cache = {"dir": None, "collection": None, "vectorizer": None}

# Matches phrases like "under 80k", "below 1 lakh", "budget of 60000", "up to 50 thousand"
_BUDGET_HINT_RE = re.compile(
    r"(?:under|below|less\s+than|cheaper\s+than|max(?:imum)?(?:\s+of)?|"
    r"up\s+to|within|budget(?:\s+of)?)\s*(?:rs\.?|npr\.?)?\s*"
    r"(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?",
    re.IGNORECASE,
)


def set_index_dir(path):
    """Point the RAG module at a different persisted index (used by tests)."""
    global INDEX_DIR
    INDEX_DIR = path
    reset_index_cache()


def reset_index_dir():
    """Restore the production index location."""
    global INDEX_DIR
    INDEX_DIR = DEFAULT_INDEX_DIR
    reset_index_cache()


def reset_index_cache():
    _cache["dir"] = None
    _cache["collection"] = None
    _cache["vectorizer"] = None


# ---------------------------------------------------------------------------
# Document construction
# ---------------------------------------------------------------------------

_CPU_WORDS = {
    1: "entry-level CPU for basic tasks",
    2: "basic mainstream CPU",
    3: "solid mid-range CPU",
    4: "fast performance CPU",
    5: "high-performance CPU",
    6: "workstation-class flagship CPU",
}


def _price_descriptor(price):
    if price <= 30000:
        return "budget cheap"
    if price <= 60000:
        return "affordable low-cost"
    if price <= 100000:
        return "mid-range"
    if price <= 150000:
        return "upper mid-range premium"
    if price <= 250000:
        return "premium high-end expensive"
    return "flagship top-of-the-line most expensive"


def _weight_descriptor(weight):
    if weight <= 0:
        return ""
    if weight < 1.3:
        return "ultralight thin-and-light highly portable"
    if weight < 1.9:
        return "lightweight portable"
    return "standard weight"


def _graphics_descriptor(gpu_brand, gpu_model):
    dedicated = (
        "integrated" not in gpu_model.lower()
        and gpu_brand.lower() not in ("intel", "unknown")
    )
    if dedicated:
        return f"dedicated {gpu_brand} graphics suitable for gaming"
    return f"integrated {gpu_brand} graphics for everyday tasks and office work"


def build_document(laptop):
    """Turn one preprocessed laptop row into an indexed natural-language doc."""
    parts = [f"{laptop['Brand']} {laptop['CPU_Brand']} laptop"]
    ct = cpu_tier(laptop["CPU_Model"])
    parts.append(f"{laptop['CPU_Model']} processor ({_CPU_WORDS[ct]}, tier {ct} of 6)")
    gt = gpu_tier(laptop["GPU_Model"])
    parts.append(
        f"{laptop['GPU_Model']} {_graphics_descriptor(laptop['GPU_Brand'], laptop['GPU_Model'])}, tier {gt} of 6"
    )
    parts.append(f"{laptop['RAM_GB']:.0f}GB RAM")
    if laptop["Storage_GB"] > 0:
        parts.append(f"{laptop['Storage_GB']:.0f}GB {laptop['Storage_Type']} storage")
    else:
        parts.append("storage capacity not listed")
    if laptop["Screen_Size_Inches"] > 0:
        size = (
            f"{laptop['Screen_Size_Inches']:.0f} inch"
            if laptop["Screen_Size_Inches"] == int(laptop["Screen_Size_Inches"])
            else f"{laptop['Screen_Size_Inches']:.1f} inch"
        )
        touch = " touchscreen" if laptop["Touchscreen"] else ""
        parts.append(f"{size}{touch} display")
    parts.append(f"runs {laptop['Operating_System']}")
    if laptop["Weight_KG"] > 0:
        parts.append(f"weighs {laptop['Weight_KG']:.1f}kg ({_weight_descriptor(laptop['Weight_KG'])})")
    price_desc = _price_descriptor(laptop["Price_NPR"])
    parts.append(f"priced at NPR {laptop['Price_NPR']:,.0f} ({price_desc})")
    purposes = ", ".join(laptop["Purpose_Labels"]) if laptop["Purpose_Labels"] else "General Use"
    parts.append(f"suited for {purposes}")
    return ". ".join(parts) + "."


# ---------------------------------------------------------------------------
# Index building / loading
# ---------------------------------------------------------------------------

def build_index(data_path=None, persist_dir=None):
    """Index every laptop in the dataset into the ChromaDB collection."""
    import chromadb
    import numpy as np
    from chromadb.config import Settings
    from sklearn.feature_extraction.text import TfidfVectorizer

    data_path = data_path or DATA_PATH
    persist_dir = os.path.abspath(persist_dir or INDEX_DIR)
    os.makedirs(persist_dir, exist_ok=True)

    laptops = preprocess(load_data(data_path))

    documents = [build_document(lt) for lt in laptops]

    # Full formatted records live in metadata so answers are always grounded
    # in dataset values (the LLM step later can quote them safely).
    metadatas = [format_laptop(lt) for lt in laptops]
    ids = [f"laptop-{i}" for i in range(len(laptops))]

    vectorizer = TfidfVectorizer(
        max_features=4000,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    embeddings = vectorizer.fit_transform(documents).toarray().astype(np.float32)

    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # first build - nothing to replace
    collection = client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    chunk = 1000
    for start in range(0, len(ids), chunk):
        end = start + chunk
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )

    with open(os.path.join(persist_dir, VECTORIZER_FILE), "wb") as f:
        pickle.dump(vectorizer, f)

    meta = {
        "collection": COLLECTION_NAME,
        "count": len(ids),
        "dimension": int(embeddings.shape[1]),
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "data_path": os.path.abspath(data_path),
    }
    with open(os.path.join(persist_dir, META_FILE), "w") as f:
        json.dump(meta, f, indent=2)

    if persist_dir == os.path.abspath(INDEX_DIR):
        _cache.update({"dir": persist_dir, "collection": collection, "vectorizer": vectorizer})

    meta["persist_dir"] = persist_dir
    return meta


def _load_index():
    """Load (and cache) the persisted collection + fitted vectorizer."""
    if _cache["collection"] is not None and _cache["dir"] == INDEX_DIR:
        return _cache["collection"], _cache["vectorizer"]

    import chromadb
    from chromadb.config import Settings

    persist_dir = os.path.abspath(INDEX_DIR)
    vec_file = os.path.join(persist_dir, VECTORIZER_FILE)
    if not os.path.isdir(persist_dir) or not os.path.isfile(vec_file):
        raise FileNotFoundError(
            f"RAG index not found at {persist_dir}. Build it first with: python3 -m model.rag"
        )

    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection(COLLECTION_NAME)
    with open(vec_file, "rb") as f:
        vectorizer = pickle.load(f)

    _cache.update({"dir": INDEX_DIR, "collection": collection, "vectorizer": vectorizer})
    return collection, vectorizer


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------

def extract_budget_hint(query):
    """Pull an explicit price cap out of free text ('under 80k' -> 80000).

    Returns None when no price phrase is present.
    """
    match = _BUDGET_HINT_RE.search(query)
    if not match:
        return None
    value = float(match.group(1))
    unit = (match.group(2) or "").lower()
    if unit in ("k", "thousand"):
        value *= 1000
    elif unit in ("lakh", "lac"):
        value *= 100000
    elif value < 10000:
        value *= 1000  # bare "under 60" almost certainly means 60k
    return value


def _build_where(brand=None, max_price=None):
    conditions = []
    if brand:
        conditions.append({"brand": {"$eq": brand}})
    if max_price is not None:
        conditions.append({"price_npr": {"$lte": float(max_price)}})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def ask(query, n_results=5, max_price=None, brand=None):
    """Retrieve the most relevant laptops from our own dataset.

    Grounded by construction: only indexed dataset rows can come back, and each
    answer carries the exact stored document + laptop record.
    """
    if query is None or not str(query).strip():
        raise ValueError("query must be a non-empty string")

    collection, vectorizer = _load_index()
    total = collection.count()
    if total == 0:
        raise FileNotFoundError("RAG index is empty. Rebuild it with: python3 -m model.rag")

    applied_max = max_price if max_price is not None else extract_budget_hint(str(query))
    n_results = max(1, min(int(n_results), total, 20))

    import numpy as np

    query_vec = vectorizer.transform([str(query)]).toarray().astype(np.float32)[0]
    result = collection.query(
        query_embeddings=[query_vec.tolist()],
        n_results=n_results,
        where=_build_where(brand=brand, max_price=applied_max),
    )

    answers = []
    for rank, (doc, meta, dist) in enumerate(
        zip(result["documents"][0], result["metadatas"][0], result["distances"][0]), start=1
    ):
        answers.append({
            "rank": rank,
            "similarity": round(max(0.0, 1.0 - float(dist)), 4),
            "distance": round(float(dist), 4),
            "laptop": {key: meta[key] for key in (
                "brand", "cpu_model", "cpu_brand", "cpu_tier",
                "gpu_model", "gpu_brand", "gpu_tier",
                "ram_gb", "storage_gb", "storage_type",
                "screen_size", "touchscreen", "os", "weight_kg",
                "price_npr", "purpose",
            )},
            "document": doc,
        })

    return {
        "status": "ok" if answers else "no_match",
        "message": (
            f"Retrieved {len(answers)} relevant laptops from the dataset index."
            if answers
            else "No laptops matched those filters. Try widening the budget or brand."
        ),
        "query": str(query),
        "max_price_applied": applied_max,
        "total_indexed": total,
        "answers": answers,
    }


if __name__ == "__main__":
    print(f"Building RAG index from {DATA_PATH} ...")
    meta = build_index()
    print(
        f"Indexed {meta['count']} laptops "
        f"(dim={meta['dimension']}) into {os.path.abspath(meta['persist_dir'])}"
    )

    demos = [
        "good gaming laptop with RTX graphics",
        "lightweight laptop for students under 50k",
        "apple macbook for video editing",
        "cheap office laptop below 40 thousand",
    ]
    for q in demos:
        res = ask(q, n_results=3)
        extra = f"  (max price applied: {res['max_price_applied']:,.0f})" if res["max_price_applied"] else ""
        print(f"\nQ: {q}{extra}")
        for ans in res["answers"]:
            lt = ans["laptop"]
            print(
                f"  #{ans['rank']} [{ans['similarity']:.3f}] {lt['brand']} | "
                f"{lt['cpu_model']} | {lt['gpu_model']} | {lt['ram_gb']:.0f}GB | "
                f"NPR {lt['price_npr']:,.0f}"
            )
