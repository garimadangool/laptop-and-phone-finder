"""RAG retrieval over the phone dataset using ChromaDB.

Index every phone as a natural-language spec-sheet document plus its full
formatted record as metadata, so free-text questions ("good camera phone
under 20k") retrieve real phones from our dataset.

Build with:  python3 -m model.rag_phones
Query via:   GET /phones/ask?query=...
"""

import json
import os
import pickle
import re
from datetime import datetime

from model.recommend_phones import (
    load_data, preprocess, format_phone, chipset_tier_score,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "phones_ml_ready.csv")
DEFAULT_INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_phones")

COLLECTION_NAME = "phones"
VECTORIZER_FILE = "vectorizer.pkl"
META_FILE = "index_meta.json"

INDEX_DIR = DEFAULT_INDEX_DIR
_cache = {"dir": None, "collection": None, "vectorizer": None}

_BUDGET_HINT_RE = re.compile(
    r"(?:under|below|less\s+than|cheaper\s+than|max(?:imum)?(?:\s+of)?|"
    r"up\s+to|within|budget(?:\s+of)?)\s*(?:rs\.?|npr\.?)?\s*"
    r"(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?",
    re.IGNORECASE,
)


def set_index_dir(path):
    global INDEX_DIR
    INDEX_DIR = path
    reset_index_cache()


def reset_index_dir():
    global INDEX_DIR
    INDEX_DIR = DEFAULT_INDEX_DIR
    reset_index_cache()


def reset_index_cache():
    _cache["dir"] = None
    _cache["collection"] = None
    _cache["vectorizer"] = None


# ── document construction ────────────────────────────────────────────────

_TIER_WORDS = {
    1: "entry-level budget chipset",
    2: "basic mainstream chipset",
    3: "mid-range chipset",
    4: "upper mid-range performance chipset",
    5: "high-performance flagship-tier chipset",
    6: "top flagship chipset",
}


def _price_descriptor(price):
    if price <= 10000:
        return "budget cheap"
    if price <= 20000:
        return "affordable low-cost"
    if price <= 40000:
        return "mid-range"
    if price <= 80000:
        return "upper mid-range premium"
    return "flagship top-of-the-line most expensive"


def build_document(phone):
    parts = [f"{phone['Brand']} phone with {phone['Chipset']} chipset"]
    tier = phone["Chipset_Tier"]
    parts.append(f"({_TIER_WORDS.get(tier, 'chipset')}, tier {tier} of 6)")
    parts.append(f"{phone['RAM_GB']:.0f}GB RAM")
    if phone["Storage_GB"] > 0:
        parts.append(f"{phone['Storage_GB']:.0f}GB {phone['Storage_Type']} storage")
    if phone["Display_Size_Inches"] > 0:
        parts.append(f"{phone['Display_Size_Inches']:.1f} inch {phone['Display_Type']} display")
    elif phone["Display_Type"] and phone["Display_Type"] != "Unknown":
        parts.append(f"{phone['Display_Type']} display")
    if phone["Rear_Camera_MP"] > 0:
        ois = " with OIS" if phone["Has_OIS"] == "Yes" else ""
        parts.append(f"{phone['Rear_Camera_MP']:.0f}MP rear camera{ois}")
    if phone["Front_Camera_MP"] > 0:
        parts.append(f"{phone['Front_Camera_MP']:.0f}MP front camera")
    if phone["Battery_mAh"] > 0:
        parts.append(f"{phone['Battery_mAh']:.0f}mAh battery")
    if phone["Fast_Charging_W"] > 0:
        parts.append(f"{phone['Fast_Charging_W']:.0f}W fast charging")
    if phone["Has_5G"] == "Yes":
        parts.append("5G support")
    if phone["Has_NFC"] == "Yes":
        parts.append("NFC")
    if phone["Has_Fingerprint"] == "Yes":
        parts.append("fingerprint sensor")
    parts.append(f"runs {phone['OS']}")
    if phone["Weight_Grams"] > 0:
        parts.append(f"weighs {phone['Weight_Grams']:.0f}g")
    parts.append(f"priced at NPR {phone['Price_NPR']:,.0f} ({_price_descriptor(phone['Price_NPR'])})")
    purposes = phone.get("Purpose", "General Use")
    parts.append(f"suited for {purposes}")
    return ". ".join(parts) + "."


# ── index building ───────────────────────────────────────────────────────

def build_index(data_path=None, persist_dir=None):
    import chromadb
    import numpy as np
    from chromadb.config import Settings
    from sklearn.feature_extraction.text import TfidfVectorizer

    data_path = data_path or DATA_PATH
    persist_dir = os.path.abspath(persist_dir or INDEX_DIR)
    os.makedirs(persist_dir, exist_ok=True)

    phones = preprocess(load_data(data_path))
    documents = [build_document(ph) for ph in phones]
    metadatas = [format_phone(ph) for ph in phones]
    ids = [f"phone-{i}" for i in range(len(phones))]

    vectorizer = TfidfVectorizer(
        max_features=4000, ngram_range=(1, 2), sublinear_tf=True,
    )
    embeddings = vectorizer.fit_transform(documents).toarray().astype(np.float32)

    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
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
    if _cache["collection"] is not None and _cache["dir"] == INDEX_DIR:
        return _cache["collection"], _cache["vectorizer"]

    import chromadb
    from chromadb.config import Settings

    persist_dir = os.path.abspath(INDEX_DIR)
    vec_file = os.path.join(persist_dir, VECTORIZER_FILE)
    if not os.path.isdir(persist_dir) or not os.path.isfile(vec_file):
        raise FileNotFoundError(
            f"Phone RAG index not found at {persist_dir}. Build it first: python3 -m model.rag_phones"
        )

    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection(COLLECTION_NAME)
    with open(vec_file, "rb") as f:
        vectorizer = pickle.load(f)

    _cache.update({"dir": INDEX_DIR, "collection": collection, "vectorizer": vectorizer})
    return collection, vectorizer


# ── querying ─────────────────────────────────────────────────────────────

def extract_budget_hint(query):
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
        value *= 1000
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
    if query is None or not str(query).strip():
        raise ValueError("query must be a non-empty string")

    collection, vectorizer = _load_index()
    total = collection.count()
    if total == 0:
        raise FileNotFoundError("Phone RAG index is empty. Rebuild: python3 -m model.rag_phones")

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
                "brand", "product_name", "chipset", "chipset_family", "chipset_tier",
                "gpu", "ram_gb", "storage_gb", "storage_type",
                "display_size", "display_type", "battery_mah", "fast_charging_w",
                "rear_camera_mp", "front_camera_mp", "has_ois",
                "has_5g", "has_nfc", "has_fingerprint",
                "weight_grams", "os", "price_npr", "purpose",
            )},
            "document": doc,
        })

    return {
        "status": "ok" if answers else "no_match",
        "message": (
            f"Retrieved {len(answers)} relevant phones from the dataset index."
            if answers
            else "No phones matched those filters. Try widening the budget or brand."
        ),
        "query": str(query),
        "max_price_applied": applied_max,
        "total_indexed": total,
        "answers": answers,
    }


if __name__ == "__main__":
    print(f"Building phone RAG index from {DATA_PATH} ...")
    meta = build_index()
    print(f"Indexed {meta['count']} phones (dim={meta['dimension']}) into {os.path.abspath(meta['persist_dir'])}")

    demos = [
        "good camera phone under 20k",
        "gaming phone with Snapdragon 8",
        "cheap student phone below 10000",
        "long battery life phone 5G",
    ]
    for q in demos:
        res = ask(q, n_results=3)
        extra = f"  (max price: {res['max_price_applied']:,.0f})" if res["max_price_applied"] else ""
        print(f"\nQ: {q}{extra}")
        for ans in res["answers"]:
            ph = ans["laptop"]
            print(f"  #{ans['rank']} [{ans['similarity']:.3f}] {ph['brand']} | {ph['chipset']} | {ph['ram_gb']:.0f}GB | {ph['battery_mah']:.0f}mAh | NPR {ph['price_npr']:,.0f}")
