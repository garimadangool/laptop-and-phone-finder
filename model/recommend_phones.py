"""Phone recommendation engine.

Content-based scoring engine for mobile phones, analogous to recommend.py
for laptops.  Scores phones on budget fit (30 %), purpose match (20 %),
chipset performance (20 %), camera quality (10 %), battery/charging (10 %),
and connectivity (10 %).

Usage:
    from model.recommend_phones import recommend_phones
    result = recommend_phones({"budget": "30000", "purpose": "camera", "top_n": 5})
"""

import csv
import math
import os
import re
from collections import defaultdict


DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "phones_ml_ready.csv"
)

ALL_PHONE_PURPOSES = [
    "Battery Life",
    "Camera",
    "Fast Performance",
    "Gaming",
    "General Use",
    "Heavy Multitasking",
    "Student",
]

PURPOSE_KEYWORD_MAP = {
    "gaming": ["Gaming"],
    "camera": ["Camera"],
    "photography": ["Camera"],
    "photo": ["Camera"],
    "fast performance": ["Fast Performance"],
    "speed": ["Fast Performance"],
    "powerful": ["Fast Performance"],
    "heavy multitasking": ["Heavy Multitasking", "Fast Performance"],
    "multitasking": ["Heavy Multitasking"],
    "student": ["Student", "General Use"],
    "studying": ["Student", "General Use"],
    "budget": ["Student", "General Use"],
    "general": ["General Use"],
    "general use": ["General Use"],
    "everyday": ["General Use"],
    "battery": ["Battery Life"],
    "battery life": ["Battery Life"],
    "long battery": ["Battery Life"],
    "battery life": ["Battery Life"],
    "long lasting": ["Battery Life"],
    "office": ["General Use", "Heavy Multitasking"],
    "business": ["General Use"],
    "social media": ["General Use"],
    "youtube": ["General Use"],
    "browsing": ["General Use"],
}


# ── scoring helpers ──────────────────────────────────────────────────────

def chipset_tier_score(tier):
    """Map 1-6 chipset tier to a 0-100 performance score."""
    return min(100, tier / 6 * 100)


def camera_score(phone):
    """Score camera quality (0-100) from rear MP + OIS."""
    mp = phone["Rear_Camera_MP"]
    ois = 1 if phone["Has_OIS"] == "Yes" else 0
    if mp >= 108:
        base = 95
    elif mp >= 64:
        base = 80
    elif mp >= 50:
        base = 70
    elif mp >= 32:
        base = 55
    elif mp >= 16:
        base = 40
    elif mp >= 8:
        base = 25
    else:
        base = 10
    bonus = 15 if ois else 0
    return min(100, base + bonus)


def battery_score(phone):
    """Score battery + charging (0-100)."""
    mah = phone["Battery_mAh"]
    fast_w = phone["Fast_Charging_W"]
    if mah >= 6000:
        base = 90
    elif mah >= 5500:
        base = 80
    elif mah >= 5000:
        base = 70
    elif mah >= 4500:
        base = 55
    elif mah >= 4000:
        base = 40
    elif mah >= 3000:
        base = 25
    else:
        base = 10
    if fast_w >= 120:
        charge_bonus = 20
    elif fast_w >= 80:
        charge_bonus = 15
    elif fast_w >= 67:
        charge_bonus = 12
    elif fast_w >= 45:
        charge_bonus = 10
    elif fast_w >= 33:
        charge_bonus = 7
    elif fast_w >= 18:
        charge_bonus = 4
    else:
        charge_bonus = 0
    return min(100, base + charge_bonus)


def connectivity_score(phone):
    """Score connectivity features (0-100): 5G, NFC, fingerprint."""
    score = 0
    if phone["Has_5G"] == "Yes":
        score += 40
    if phone["Has_NFC"] == "Yes":
        score += 30
    if phone["Has_Fingerprint"] == "Yes":
        score += 30
    return score


def parse_user_budget(raw):
    raw = raw.strip().replace(",", "").replace(" ", "")
    match = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not match:
        return None
    val = float(match.group(1))
    if "lakh" in raw.lower() or "lac" in raw.lower():
        val *= 100000
    elif "k" in raw.lower():
        val *= 1000
    if val < 1000:
        val *= 100000
    return val


def parse_user_purpose(raw):
    raw_lower = raw.lower().strip()
    labels = set()
    for keyword, mapped in PURPOSE_KEYWORD_MAP.items():
        if keyword in raw_lower:
            for l in mapped:
                labels.add(l)
    if not labels:
        labels.add("General Use")
    return labels


# ── core scoring ─────────────────────────────────────────────────────────

def score_phone(phone, user):
    """Score a phone against user preferences. Returns (score, reasons, penalties)."""
    score = 0.0
    reasons = []
    penalties = []

    price = phone["Price_NPR"]
    budget = user.get("budget", 0)

    # ── Budget fit (30%) ──
    if budget > 0:
        if price <= budget:
            ratio = price / budget
            if ratio >= 0.6:
                budget_score = 100
                reasons.append("Great value within your budget")
            elif ratio >= 0.3:
                budget_score = 80 + (ratio - 0.3) * 66.7
                reasons.append("Good value within your budget")
            else:
                budget_score = 40 + ratio * 133.3
                reasons.append("Well under budget (may be lower spec)")
        else:
            over_pct = (price - budget) / budget
            if over_pct <= 0.15:
                budget_score = 50 - over_pct * 200
                reasons.append(f"Close to budget ({over_pct*100:.0f}% over)")
            elif over_pct <= 0.30:
                budget_score = 20 - over_pct * 50
                reasons.append(f"Slightly over budget ({over_pct*100:.0f}% over)")
            else:
                budget_score = max(0, 10 - over_pct * 20)
                penalties.append(f"Significantly over budget ({over_pct*100:.0f}% over)")
    else:
        budget_score = 50
    score += budget_score * 0.30

    # ── Purpose match (20%) ──
    purpose_labels = user.get("purpose_labels", set())
    phone_purposes = set(p for p in phone["Purpose"].split(", ") if p)
    if purpose_labels:
        overlap = purpose_labels & phone_purposes
        if overlap:
            purpose_score = min(100, (len(overlap) / len(purpose_labels)) * 100)
            matched = ", ".join(sorted(overlap))
            reasons.append(f"Matches your purpose: {matched}")
        else:
            purpose_score = 20
            penalties.append("Purpose doesn't directly match")
    else:
        purpose_score = 50
    score += purpose_score * 0.20

    # ── Chipset performance (20%) ──
    ctier = phone["Chipset_Tier"]
    min_tier = user.get("min_chipset_tier", 0)
    spec_score = chipset_tier_score(ctier)
    if min_tier > 0:
        if ctier >= min_tier:
            spec_score = min(100, 50 + (ctier - min_tier + 1) * 10)
            reasons.append(f"Chipset tier {ctier}/6 meets requirement")
        else:
            spec_score = (ctier / min_tier) * 50
            penalties.append(f"Chipset tier {ctier}/6 below requested tier {min_tier}/6")
    score += spec_score * 0.20

    # ── Camera quality (10%) ──
    cam_score = camera_score(phone)
    if user.get("min_camera_mp", 0) > 0:
        min_mp = user["min_camera_mp"]
        if phone["Rear_Camera_MP"] >= min_mp:
            reasons.append(f"{phone['Rear_Camera_MP']}MP camera meets {min_mp}MP requirement")
        else:
            penalties.append(f"Camera {phone['Rear_Camera_MP']}MP below requested {min_mp}MP")
    if phone["Has_OIS"] == "Yes":
        cam_score = min(100, cam_score + 5)
        reasons.append("OIS for stable shots")
    score += cam_score * 0.10

    # ── Battery + charging (10%) ──
    bat_score = battery_score(phone)
    if user.get("min_battery", 0) > 0:
        min_bat = user["min_battery"]
        if phone["Battery_mAh"] >= min_bat:
            reasons.append(f"{phone['Battery_mAh']}mAh battery meets {min_bat}mAh requirement")
        else:
            penalties.append(f"Battery {phone['Battery_mAh']}mAh below requested {min_bat}mAh")
    score += bat_score * 0.10

    # ── Connectivity (10%) ──
    conn_score = connectivity_score(phone)
    if user.get("require_5g") and phone["Has_5G"] != "Yes":
        penalties.append("No 5G support")
        conn_score = max(0, conn_score - 40)
    elif phone["Has_5G"] == "Yes":
        reasons.append("5G ready")

    if user.get("require_nfc") and phone["Has_NFC"] != "Yes":
        penalties.append("No NFC")
        conn_score = max(0, conn_score - 30)

    if user.get("require_fingerprint") and phone["Has_Fingerprint"] != "Yes":
        penalties.append("No fingerprint sensor")
        conn_score = max(0, conn_score - 30)
    score += conn_score * 0.10

    # ── Brand bonus ──
    preferred_brand = user.get("brand", "")
    if preferred_brand:
        if phone["Brand"].lower() == preferred_brand.lower():
            score += 3
            reasons.append(f"{phone['Brand']} matches your brand preference")
        else:
            penalties.append(f"Brand is {phone['Brand']}, not {preferred_brand}")
            score = max(0, score - 25)

    # ── RAM bonus ──
    ram = phone["RAM_GB"]
    min_ram = user.get("min_ram", 0)
    if min_ram > 0:
        if ram >= min_ram:
            reasons.append(f"{ram:.0f}GB RAM meets your {min_ram:.0f}GB requirement")
        else:
            penalties.append(f"RAM ({ram:.0f}GB) is below requested ({min_ram:.0f}GB)")
    if ram >= 12:
        score += 3
    elif ram >= 8:
        score += 2

    # ── Storage bonus ──
    storage = phone["Storage_GB"]
    min_storage = user.get("min_storage", 0)
    if min_storage > 0:
        if storage >= min_storage:
            reasons.append(f"{storage:.0f}GB storage meets requirement")
        else:
            penalties.append(f"Storage ({storage:.0f}GB) below requested ({min_storage:.0f}GB)")
    if storage >= 256:
        score += 2
    elif storage >= 128:
        score += 1

    score = max(0, min(100, score))
    return score, reasons, penalties


# ── formatting ───────────────────────────────────────────────────────────

def format_phone(phone):
    return {
        "brand": phone["Brand"],
        "product_name": phone["Product_Name"],
        "chipset": phone["Chipset"],
        "chipset_family": phone["Chipset_Family"],
        "chipset_tier": phone["Chipset_Tier"],
        "gpu": phone["GPU"],
        "ram_gb": phone["RAM_GB"],
        "storage_gb": phone["Storage_GB"],
        "storage_type": phone["Storage_Type"],
        "display_size": phone["Display_Size_Inches"],
        "display_type": phone["Display_Type"],
        "battery_mah": phone["Battery_mAh"],
        "fast_charging_w": phone["Fast_Charging_W"],
        "rear_camera_mp": phone["Rear_Camera_MP"],
        "front_camera_mp": phone["Front_Camera_MP"],
        "has_ois": phone["Has_OIS"],
        "has_5g": phone["Has_5G"],
        "has_nfc": phone["Has_NFC"],
        "has_fingerprint": phone["Has_Fingerprint"],
        "weight_grams": phone["Weight_Grams"],
        "os": phone["OS"],
        "price_npr": phone["Price_NPR"],
        "original_price": phone["Original_Price"],
        "purpose": phone["Purpose"],
    }


# ── deal detection ───────────────────────────────────────────────────────

def _deal_context(phones):
    bands = defaultdict(list)
    for ph in phones:
        price = ph["Price_NPR"]
        if price <= 0:
            continue
        tier = max(1, ph["Chipset_Tier"])
        ram = ph["RAM_GB"]
        band = 12 if ram >= 12 else 8 if ram >= 8 else 4
        bands[(tier, band)].append(price)

    all_prices = [p for prices in bands.values() for p in prices]
    global_median = sorted(all_prices)[len(all_prices) // 2] if all_prices else 0
    medians = {}
    for key, prices in bands.items():
        prices_sorted = sorted(prices)
        medians[key] = prices_sorted[len(prices_sorted) // 2]
    return medians, global_median


def _classify_deal(phone, deal_context):
    medians, global_median = deal_context
    price = phone["Price_NPR"]
    if price <= 0 or global_median <= 0:
        return False, "fair", ""
    tier = max(1, phone["Chipset_Tier"])
    ram = phone["RAM_GB"]
    band = 12 if ram >= 12 else 8 if ram >= 8 else 4
    key = (tier, band)
    comparator = medians.get(key, global_median)
    ratio = price / comparator
    if ratio <= 0.85:
        return True, "great", "Priced well below comparable phones"
    if ratio <= 0.97:
        return True, "good", "Competitively priced for its specs"
    if ratio <= 1.1:
        return False, "fair", ""
    return False, "premium", "Priced at a premium for its specs"


# ── data loading ─────────────────────────────────────────────────────────

def load_data(path=None):
    if path is None:
        path = DATA_PATH
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def preprocess(rows):
    cleaned = []
    for r in rows:
        row = dict(r)
        for col in ["Brand", "Chipset", "GPU", "OS", "Storage_Type"]:
            if not row.get(col) or not row[col].strip():
                row[col] = "Unknown"
        for col, default in [
            ("RAM_GB", 0.0), ("Storage_GB", 0.0), ("Display_Size_Inches", 0.0),
            ("Battery_mAh", 0.0), ("Fast_Charging_W", 0.0),
            ("Rear_Camera_MP", 0.0), ("Front_Camera_MP", 0.0),
            ("Weight_Grams", 0.0), ("Price_NPR", 0.0), ("Original_Price", 0.0),
        ]:
            try:
                row[col] = float(row[col]) if row.get(col) and str(row[col]).strip() else default
            except (ValueError, TypeError):
                row[col] = default
        for col in ["Chipset_Tier"]:
            try:
                row[col] = int(float(row[col])) if row.get(col) and str(row[col]).strip() else 1
            except (ValueError, TypeError):
                row[col] = 1
        for col in ["Has_5G", "Has_NFC", "Has_Fingerprint", "Has_OIS"]:
            row[col] = "Yes" if row.get(col, "").strip().lower().startswith("yes") else "No"
        cleaned.append(row)
    return cleaned


# ── main recommend function ──────────────────────────────────────────────

def recommend_phones(user_input, top_n=5, data_path=None):
    rows = load_data(data_path)
    phones = preprocess(rows)

    _budget = parse_user_budget(str(user_input.get("budget", "")))
    budget = _budget if _budget is not None else 0
    purpose_raw = user_input.get("purpose", "General Use")
    purpose_labels = parse_user_purpose(purpose_raw)

    user = {
        "budget": budget or 0,
        "purpose_labels": purpose_labels,
        "purpose_raw": purpose_raw,
        "min_ram": float(user_input.get("min_ram", 0) or 0),
        "min_storage": float(user_input.get("min_storage", 0) or 0),
        "min_chipset_tier": int(user_input.get("min_chipset_tier", 0) or 0),
        "min_camera_mp": int(user_input.get("min_camera_mp", 0) or 0),
        "min_battery": int(user_input.get("min_battery", 0) or 0),
        "brand": user_input.get("brand", ""),
        "require_5g": user_input.get("require_5g", False),
        "require_nfc": user_input.get("require_nfc", False),
        "require_fingerprint": user_input.get("require_fingerprint", False),
    }

    scored = []
    for phone in phones:
        if budget > 0 and phone["Price_NPR"] > budget * 1.5:
            continue
        if user["min_ram"] > 0 and phone["RAM_GB"] < user["min_ram"] * 0.5:
            continue
        if user["min_storage"] > 0 and phone["Storage_GB"] < user["min_storage"] * 0.5:
            continue
        if user["require_5g"] and phone["Has_5G"] != "Yes":
            continue
        if user["require_fingerprint"] and phone["Has_Fingerprint"] != "Yes":
            continue
        if user["brand"] and phone["Brand"].lower() != user["brand"].lower():
            continue

        s, reasons, penalties = score_phone(phone, user)
        scored.append({
            "phone": phone,
            "score": round(s, 2),
            "reasons": reasons,
            "penalties": penalties,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    deal_ctx = _deal_context(phones)

    def _annotated(item):
        is_deal, deal_tier, deal_note = _classify_deal(item["phone"], deal_ctx)
        return {
            "laptop": format_phone(item["phone"]),
            "score": item["score"],
            "reasons": item["reasons"],
            "penalties": item["penalties"],
            "deal": {"is_deal": is_deal, "tier": deal_tier, "note": deal_note},
        }

    if not scored:
        closest = sorted(phones, key=lambda x: x["Price_NPR"])
        if user["brand"]:
            closest = [p for p in closest if p["Brand"].lower() == user["brand"].lower()]
        if budget > 0:
            below = [p for p in closest if p["Price_NPR"] <= budget]
            above = [p for p in closest if p["Price_NPR"] > budget]
            fallback_pool = below[-5:] if below else above[:5]
        else:
            fallback_pool = closest[:5]
        result = []
        for phone in fallback_pool:
            s, reasons, penalties = score_phone(phone, user)
            reasons.insert(0, "Closest alternative (no exact match found)")
            result.append(_annotated({
                "phone": phone,
                "score": round(s, 2),
                "reasons": reasons,
                "penalties": penalties,
            }))
        return {
            "status": "no_exact_match",
            "message": "No phones exactly match your criteria. Showing closest alternatives.",
            "recommendations": result,
            "user_query": {
                "budget": budget,
                "purpose": purpose_raw,
                "purpose_labels": list(purpose_labels),
            },
        }

    top = scored[:top_n]
    result = [_annotated(item) for item in top]
    return {
        "status": "ok",
        "message": f"Found {len(scored)} matching phones. Showing top {len(result)}.",
        "recommendations": result,
        "user_query": {
            "budget": budget,
            "purpose": purpose_raw,
            "purpose_labels": list(purpose_labels),
        },
    }


# ── stats & insights ────────────────────────────────────────────────────

def get_phone_stats(data_path=None):
    phones = preprocess(load_data(data_path))
    brands = defaultdict(int)
    purposes = defaultdict(int)
    for ph in phones:
        brands[ph["Brand"]] += 1
        for p in ph["Purpose"].split(", "):
            if p:
                purposes[p] += 1
    prices = [ph["Price_NPR"] for ph in phones if ph["Price_NPR"] > 0]
    return {
        "total_phones": len(phones),
        "brands": dict(sorted(brands.items(), key=lambda x: -x[1])),
        "purpose_distribution": dict(sorted(purposes.items(), key=lambda x: -x[1])),
        "price_range": {
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0,
            "avg": sum(prices) / len(prices) if prices else 0,
        },
    }


def get_phone_insights(data_path=None):
    phones = preprocess(load_data(data_path))
    total = len(phones)
    prices = [ph["Price_NPR"] for ph in phones if ph["Price_NPR"] > 0]

    price_histogram = []
    step = 5000
    for start in range(0, 150000, step):
        end = start + step
        price_histogram.append({
            "bucket": f"{start // 1000}K-{end // 1000}K",
            "count": sum(1 for p in prices if start <= p < end),
        })
    price_histogram.append({"bucket": "150K+", "count": sum(1 for p in prices if p >= 150000)})
    while price_histogram and price_histogram[0]["count"] == 0:
        price_histogram.pop(0)

    brand_counts = defaultdict(int)
    purpose_counts = defaultdict(int)
    tier_counts = defaultdict(int)
    family_counts = defaultdict(int)
    battery_groups = defaultdict(list)
    camera_counts = defaultdict(int)

    for ph in phones:
        brand_counts[ph["Brand"]] += 1
        for p in ph["Purpose"].split(", "):
            if p:
                purpose_counts[p] += 1
        tier_counts[ph["Chipset_Tier"]] += 1
        family_counts[ph["Chipset_Family"]] += 1
        if ph["Battery_mAh"] > 0:
            bat_band = int(ph["Battery_mAh"] // 1000)
            battery_groups[bat_band].append(ph["Price_NPR"])
        cam = ph["Rear_Camera_MP"]
        if cam >= 108:
            camera_counts["108MP+"] += 1
        elif cam >= 64:
            camera_counts["64MP"] += 1
        elif cam >= 50:
            camera_counts["50MP"] += 1
        elif cam >= 32:
            camera_counts["32MP"] += 1
        elif cam >= 16:
            camera_counts["16MP"] += 1
        else:
            camera_counts["<16MP"] += 1

    fiveg_count = sum(1 for ph in phones if ph["Has_5G"] == "Yes")
    nfc_count = sum(1 for ph in phones if ph["Has_NFC"] == "Yes")

    return {
        "total_phones": total,
        "positive_price_count": len(prices),
        "price_histogram": price_histogram,
        "top_brands": [
            {"brand": b, "count": c}
            for b, c in sorted(brand_counts.items(), key=lambda x: -x[1])[:10]
        ],
        "purpose_distribution": [
            {"purpose": p, "count": c}
            for p, c in sorted(purpose_counts.items(), key=lambda x: -x[1])
        ],
        "chipset_tier_distribution": [
            {"tier": t, "count": tier_counts.get(t, 0)} for t in range(1, 7)
        ],
        "chipset_family_distribution": [
            {"family": f, "count": c}
            for f, c in sorted(family_counts.items(), key=lambda x: -x[1])
        ],
        "camera_distribution": [
            {"category": cat, "count": c}
            for cat, c in sorted(camera_counts.items(), key=lambda x: -x[1])
        ],
        "fiveg_count": fiveg_count,
        "nfc_count": nfc_count,
    }


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        {"budget": "20000", "purpose": "camera", "min_ram": 6},
        {"budget": "30000", "purpose": "gaming", "min_chipset_tier": 4, "require_5g": True},
        {"budget": "10000", "purpose": "student"},
        {"budget": "50000", "purpose": "fast performance and heavy multitasking", "min_ram": 12},
        {"budget": "15000", "purpose": "battery life"},
    ]
    for i, tc in enumerate(test_cases, 1):
        print(f"\nTEST {i}: Budget={tc['budget']}, Purpose={tc['purpose']}")
        result = recommend_phones(tc, top_n=3)
        print(f"Status: {result['status']} | {result['message']}")
        for j, rec in enumerate(result["recommendations"], 1):
            ph = rec["laptop"]
            print(f"  #{j} [{rec['score']}pts] {ph['brand']} {ph['product_name'][:40]}")
            print(f"     Chipset: {ph['chipset']} (tier {ph['chipset_tier']}) | {ph['ram_gb']:.0f}GB RAM | {ph['storage_gb']:.0f}GB | {ph['battery_mah']:.0f}mAh")
            print(f"     Camera: {ph['rear_camera_mp']:.0f}MP | 5G: {ph['has_5g']} | NFC: {ph['has_nfc']}")
            print(f"     Price: NPR {ph['price_npr']:,.0f}")
