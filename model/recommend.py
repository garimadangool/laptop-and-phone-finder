import csv
import math
import re
import os


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "laptops_ml_ready.csv")


ALL_PURPOSE_LABELS = [
    "AI / Machine Learning",
    "Fast Performance",
    "Gaming",
    "General Use",
    "Graphic Design",
    "Heavy Multitasking",
    "Office",
    "Programming",
    "Student",
    "Video Editing",
]

PURPOSE_KEYWORD_MAP = {
    "gaming": ["Gaming"],
    "programming": ["Programming"],
    "editing": ["Video Editing", "Graphic Design"],
    "graphic design": ["Graphic Design"],
    "video editing": ["Video Editing"],
    "studying": ["Student", "General Use", "Programming"],
    "student": ["Student", "General Use"],
    "office": ["Office", "General Use"],
    "office work": ["Office", "General Use"],
    "ai": ["AI / Machine Learning"],
    "machine learning": ["AI / Machine Learning"],
    "data science": ["AI / Machine Learning", "Heavy Multitasking"],
    "general": ["General Use"],
    "general use": ["General Use"],
    "heavy multitasking": ["Heavy Multitasking", "Fast Performance"],
    "fast performance": ["Fast Performance"],
    "design": ["Graphic Design", "Video Editing"],
}

CPU_TIERS = {
    1: [
        "celeron", "pentium", "athlon", "a4-", "a6-", "a9-", "e2-",
        "atom", "pentium silver", "pentium gold", "celeron dual",
        "pentium quad", "pentium dual", "3020e", "n100", "n50",
        "processor n150", "processor n100", "processor n200",
        "kompanio", "snapdragon 7c", "mediatek",
    ],
    2: [
        "core i3", "ryzen 3", "a10-", "a12-",
        "core 3 ", "athlon silver", "athlon gold",
    ],
    3: [
        "core i5 6", "core i5 7", "core i5 8", "core i5 10",
        "core i5-10", "core i5-1135g7", "core i5-11300h",
        "core i5-1235u", "core i5-12450h",
        "ryzen 5 3", "ryzen 5 4", "ryzen 5 2",
        "core m3", "core m5", "core m7",
        "core 5 120u", "core 5 210u", "core 5 210h",
        "ryzen ai 5",
        "snapdragon x plus x1p-42",
    ],
    4: [
        "core i5-1334u", "core i5-1335u", "core i5-13420h",
        "core i5-13500h", "core i5-13450hx", "core i5-14450hx",
        "13th gen core i5", "14th gen core i5",
        "12th gen core i5 12450hx", "12th gen core i5 12500h",
        "core i7 6", "core i7 7", "core i7 8",
        "core i7-8550u", "core i7-11370h", "core i7-1165g7",
        "core i7-11800h", "core i7-1185g7", "core i7-1195g7",
        "core i7-1255u", "core i7-1260p", "core i7-12650h",
        "core i7-12700h",
        "ryzen 5 5", "ryzen 5 6", "ryzen 5 7",
        "ryzen 7 3", "ryzen 7 4", "ryzen 7 2",
        "ryzen 7 5700u", "ryzen 7 5800h", "ryzen 7 6800h",
        "ryzen 7 7730u", "ryzen 7 7735u", "ryzen 7 7840hs",
        "snapdragon x elite x1e-78",
        "snapdragon x plus x1p-64",
    ],
    5: [
        "core i7-1355u", "core i7-13620h", "core i7-13650hx",
        "core i7-13700h", "core i7-13700hx", "core i7-14650hx",
        "core i7-14700hx",
        "13th gen core i7 13620h", "13th gen core i7 13700h",
        "13th gen core i7 1355u", "13th gen core i7 13650hx",
        "14th gen core i7 14650hx", "14th gen core i7 14700hx",
        "12th gen core i7 12700h", "12th gen core i7 12650h",
        "core ultra 5", "core ultra 7 155h", "core ultra 7 155u",
        "core ultra 7 165u", "core ultra 7 165h",
        "core ultra 7 255h", "core ultra 7 255u", "core ultra 7 255hx",
        "core ultra 7 256v", "core ultra 7 258v", "core ultra 7 265u",
        "core ultra 7 265h", "core ultra 7 265hx", "core ultra 7 266v",
        "core ultra 7 268v", "core ultra 7 355", "core ultra 7 356h",
        "core ultra 7 series",
        "core ultra 9 185h", "core ultra 9 275hx", "core ultra 9 285h",
        "core ultra 9 285hx", "core ultra 9 288v", "core ultra 9 386h",
        "core ultra 9 series",
        "core 7 150u", "core 7 240h", "core 7 series",
        "core 9 270h",
        "ryzen 7 5800h", "ryzen 7 6800h", "ryzen 7 6800hs",
        "ryzen 7 7735hs", "ryzen 7 7840hs", "ryzen 7 7445hs",
        "ryzen 7 7445h", "ryzen 7 7730u", "ryzen 7 7435hs",
        "ryzen 7 7840u", "ryzen 7 8840hs", "ryzen 7 8840u",
        "ryzen 7 8840hx", "ryzen 7 8845hs",
        "ryzen 7-5800h", "ryzen 7-6800h", "ryzen 7-6800hs",
        "ryzen 9 5900h", "ryzen 9 5900hs", "ryzen 9 5900hx",
        "ryzen 9 5980hs", "ryzen 9 6900h", "ryzen 9 6900hx",
        "ryzen 9 6900hs",
        "core i9 10", "core i9-10", "core i9 11", "core i9-11900h",
        "core i9-11980hk",
        "snapdragon x elite", "snapdragon x x1",
    ],
    6: [
        "core i9-12900h", "core i9-12900hk", "core i9-12950hx",
        "core i9-13900h", "core i9-13900hk", "core i9-13900hx",
        "core i9-13950hx", "core i9-13980hx",
        "core i9-14900hx",
        "13th gen core i9 13900h", "13th gen core i9 13900hx",
        "13th gen core i9 13980hx",
        "14th gen core i9 14900hx",
        "core ultra 9 275hx", "core ultra 9 285hx",
        "core ultra 9 386h",
        "core ultra x7 358h", "core ultra x9 388h",
        "ryzen 9 7945hx", "ryzen 9 8940hx", "ryzen 9 8945hs",
        "ryzen 9 8945hx", "ryzen 9 9955hx", "ryzen 9 9955hx3d",
        "ryzen ai 9 365", "ryzen ai 9 465", "ryzen ai 9 hx 370",
        "ryzen ai 9 hx 375", "ryzen ai 9 hx pro 370",
        "ryzen ai 9 hx pro 375", "ryzen ai 9 hx pro 375",
        "ryzen ai max", "ryzen ai max+",
        "threadripper",
        "apple m1", "apple m2", "apple m3", "apple m4",
        "apple m5",
        "snapdragon x elite x1e-80",
    ],
}

GPU_TIERS = {
    1: [
        "radeon r2", "radeon r3", "radeon r4", "radeon r5 ",
        "radeon r5 m", "radeon r7 m430", "radeon r7 m440",
        "radeon r7 m445", "radeon r7 m460", "radeon r7 m465",
        "radeon r7 m360", "radeon r7 m365", "radeon rx vega 3",
        "radeon rx vega 6",
        "hd graphics 400", "hd graphics 405", "hd graphics 500",
        "hd graphics 505", "hd graphics 510", "hd graphics 515",
        "hd graphics 530", "hd graphics 600",
        "uhd graphics (jasper", "uhd graphics 600",
        "radeon 610m", "radeon 630", "radeon 740m",
        "radeon 820m", "radeon 840m",
        "qualcomm adreno gpu", "qualcomm adreno 618",
        "arm mali",
    ],
    2: [
        "hd graphics 520", "hd graphics 540", "hd graphics 610",
        "hd graphics 615", "hd graphics 620", "hd graphics 630",
        "uhd graphics 620", "uhd graphics",
        "iris plus graphics 640", "iris plus graphics 650",
        "iris xe graphics g7 (80eu)",
        "iris graphics 540", "iris graphics 550",
        "radeon 520", "radeon 530", "radeon 540",
        "radeon 860m", "radeon 780m", "radeon 680m",
        "radeon 880m", "radeon 890m",
        "geforce 920m", "geforce 920mx", "geforce 930m", "geforce 930mx",
        "geforce 940m", "geforce 940mx",
        "geforce mx130", "geforce mx150", "geforce mx230",
        "geforce mx330", "geforce mx350", "geforce mx450",
        "geforce mx550", "geforce mx570",
        "geforce 150mx",
        "geforce gtx 940m", "geforce gtx 940mx",
        "geforce gtx 950m", "geforce gtx 960m",
        "geforce gtx 965m",
        "integrated", "integrated uhd",
        "iris plus", "iris xe",
        "qualcomm snapdragon x elite adreno",
        "qualcomm sd x adreno",
    ],
    3: [
        "iris xe graphics g7 (96eu)", "iris xe graphics",
        "uhd graphics (alder",
        "geforce gtx 1050", "geforce gtx 1050 ti",
        "geforce gtx 1650", "geforce gtx 1650 ti",
        "geforce rtx 2050",
        "geforce rtx 3050 ", "geforce rtx 3050", "geforce rtx 3050a",
        "geforce rtx 3050ti", "geforce rtx3050",
        "radeon rx 550", "radeon rx 560", "radeon rx 580",
        "radeon rx 6500m",
        "arc a350m", "arc a370m",
        "radeon 8060s",
        "geforce gtx 970m", "geforce gtx 980m",
        "geforce gtx 980",
    ],
    4: [
        "geforce rtx 3050 4gb", "geforce rtx 3050 6gb",
        "geforce rtx 3050 ti", "geforce rtx 3050ti 4gb",
        "geforce gtx 1060", "geforce gtx 1070",
        "geforce gtx 1080", "geforce gtx 1660 ti",
        "geforce rtx 3060 6gb",
        "geforce rtx 4050 ", "geforce rtx4050",
        "geforce rtx 5050",
        "radeon rx 6600m", "radeon rx 6700s",
        "rtx pro 500", "rtx pro 1000",
        "arc (7-cores)", "arc (8-cores)",
    ],
    5: [
        "geforce rtx 3060", "geforce rtx 3070", "geforce rtx 3070 ti",
        "geforce rtx 3080", "geforce rtx 3080 ti",
        "geforce rtx 4060", "geforce rtx 4070",
        "geforce rtx 5060", "geforce rtx 5070",
        "geforce rtx 5070 ti",
        "rtx pro 2000", "rtx pro 3000", "rtx pro 4000",
        "arc b390", "arc a550", "arc a750", "arc a770",
    ],
    6: [
        "geforce rtx 4080", "geforce rtx 4090",
        "geforce rtx 5080", "geforce rtx 5090",
        "radeon rx 7600", "radeon rx 7700", "radeon rx 7800",
        "radeon rx 7900", "radeon rx 6700",
        "apple m4", "apple m5", "apple m3", "apple m2", "apple m1",
        "rtx pro 5000",
    ],
}


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

        for col in ["Brand", "CPU_Model", "CPU_Brand", "GPU_Model", "GPU_Brand", "Storage_Type", "Operating_System"]:
            if not row.get(col) or not row[col].strip():
                row[col] = "Unknown"

        if row["GPU_Model"] == "Unknown":
            row["GPU_Model"] = "Integrated"

        for col, default in [("RAM_GB", 0.0), ("Storage_GB", 0.0), ("Screen_Size_Inches", 0.0),
                             ("Weight_KG", 0.0), ("Touchscreen", 0.0), ("Price_NPR", 0.0)]:
            try:
                row[col] = float(row[col]) if row.get(col) and row[col].strip() else default
            except ValueError:
                row[col] = default

        row["Purpose_Labels"] = [p.strip() for p in row["Purpose"].split(",") if p.strip()]
        cleaned.append(row)
    return cleaned


def _match_tier(text, tier_map):
    text_lower = text.lower()
    best = 0
    for tier, patterns in tier_map.items():
        for pat in patterns:
            if pat in text_lower:
                best = max(best, tier)
    return best if best > 0 else 1


def cpu_tier(cpu_model):
    return _match_tier(cpu_model, CPU_TIERS)


def gpu_tier(gpu_model):
    return _match_tier(gpu_model, GPU_TIERS)


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


def score_laptop(laptop, user):
    score = 0.0
    reasons = []
    penalties = []

    price = laptop["Price_NPR"]
    budget = user.get("budget", 0)

    if budget > 0:
        if price <= budget:
            budget_ratio = price / budget
            if budget_ratio >= 0.6:
                budget_score = 100
                reasons.append("Great value within your budget")
            elif budget_ratio >= 0.3:
                budget_score = 80 + (budget_ratio - 0.3) * 66.7
                reasons.append("Good value within your budget")
            else:
                budget_score = 40 + budget_ratio * 133.3
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

    score += budget_score * 0.35

    purpose_labels = user.get("purpose_labels", set())
    laptop_purposes = set(laptop["Purpose_Labels"])
    if purpose_labels:
        overlap = purpose_labels & laptop_purposes
        if overlap:
            purpose_score = min(100, (len(overlap) / len(purpose_labels)) * 100)
            matched = ", ".join(sorted(overlap))
            reasons.append(f"Matches your purpose: {matched}")
        else:
            purpose_score = 20
            penalties.append("Purpose doesn't directly match")
    else:
        purpose_score = 50

    score += purpose_score * 0.25

    specs_score = 0
    spec_count = 0

    min_ram = user.get("min_ram", 0)
    spec_count += 1
    if min_ram > 0:
        if laptop["RAM_GB"] >= min_ram:
            ram_score = min(100, (laptop["RAM_GB"] / min_ram) * 50 + 50)
            reasons.append(f"{laptop['RAM_GB']:.0f}GB RAM meets your {min_ram:.0f}GB requirement")
        else:
            ram_score = (laptop["RAM_GB"] / min_ram) * 50
            penalties.append(f"RAM ({laptop['RAM_GB']:.0f}GB) is below requested ({min_ram:.0f}GB)")
        specs_score += ram_score
    else:
        if laptop["RAM_GB"] >= 16:
            specs_score += 80
        elif laptop["RAM_GB"] >= 8:
            specs_score += 50
        else:
            specs_score += 25

    min_storage = user.get("min_storage", 0)
    spec_count += 1
    if min_storage > 0:
        if laptop["Storage_GB"] >= min_storage:
            storage_score = min(100, (laptop["Storage_GB"] / min_storage) * 50 + 50)
            reasons.append(f"{laptop['Storage_GB']:.0f}GB {laptop['Storage_Type']} meets requirement")
        else:
            storage_score = (laptop["Storage_GB"] / min_storage) * 50 if laptop["Storage_GB"] > 0 else 20
            if laptop["Storage_GB"] > 0:
                penalties.append(f"Storage ({laptop['Storage_GB']:.0f}GB) below requested ({min_storage:.0f}GB)")
        specs_score += storage_score
    else:
        if laptop["Storage_GB"] > 0:
            specs_score += 50
        else:
            specs_score += 20

    user_cpu_tier = user.get("min_cpu_tier", 0)
    lt_cpu_tier = cpu_tier(laptop["CPU_Model"])
    spec_count += 1
    if user_cpu_tier > 0:
        if lt_cpu_tier >= user_cpu_tier:
            specs_score += min(100, 50 + (lt_cpu_tier - user_cpu_tier + 1) * 10)
            reasons.append(f"CPU tier {lt_cpu_tier}/6 meets requirement")
        else:
            specs_score += (lt_cpu_tier / user_cpu_tier) * 50
            penalties.append(f"CPU tier {lt_cpu_tier}/6 below requested tier {user_cpu_tier}/6")
    else:
        specs_score += min(100, lt_cpu_tier / 6 * 100)

    user_gpu_tier = user.get("min_gpu_tier", 0)
    lt_gpu_tier = gpu_tier(laptop["GPU_Model"])
    spec_count += 1
    if user_gpu_tier > 0:
        if lt_gpu_tier >= user_gpu_tier:
            specs_score += min(100, 50 + (lt_gpu_tier - user_gpu_tier + 1) * 10)
            reasons.append(f"GPU tier {lt_gpu_tier}/6 meets requirement")
        else:
            specs_score += (lt_gpu_tier / user_gpu_tier) * 50
            penalties.append(f"GPU tier {lt_gpu_tier}/6 below requested tier {user_gpu_tier}/6")
    else:
        specs_score += min(100, lt_gpu_tier / 6 * 100)

    preferred_brand = user.get("brand")
    if preferred_brand:
        spec_count += 1
        if laptop["Brand"].lower() == preferred_brand.lower():
            specs_score += 100
            reasons.append(f"{laptop['Brand']} matches your brand preference")
        else:
            specs_score += 10
            penalties.append(f"Brand is {laptop['Brand']}, not {preferred_brand}")

    avg_specs = specs_score / max(spec_count, 1)
    score += avg_specs * 0.35

    lt_cpu = cpu_tier(laptop["CPU_Model"])
    lt_gpu = gpu_tier(laptop["GPU_Model"])
    balance = 100 - abs(lt_cpu - lt_gpu) * 15
    score += max(0, balance) * 0.05

    score = max(0, min(100, score))

    return score, reasons, penalties


def format_laptop(laptop):
    return {
        "brand": laptop["Brand"],
        "cpu_model": laptop["CPU_Model"],
        "cpu_brand": laptop["CPU_Brand"],
        "cpu_tier": cpu_tier(laptop["CPU_Model"]),
        "gpu_model": laptop["GPU_Model"],
        "gpu_brand": laptop["GPU_Brand"],
        "gpu_tier": gpu_tier(laptop["GPU_Model"]),
        "ram_gb": laptop["RAM_GB"],
        "storage_gb": laptop["Storage_GB"],
        "storage_type": laptop["Storage_Type"],
        "screen_size": laptop["Screen_Size_Inches"],
        "touchscreen": bool(laptop["Touchscreen"]),
        "os": laptop["Operating_System"],
        "weight_kg": laptop["Weight_KG"],
        "price_npr": laptop["Price_NPR"],
        "purpose": laptop["Purpose"],
    }


def _deal_context(laptops):
    """Build a median-price lookup keyed by (cpu_tier, gpu_tier, ram_band).

    Used to flag whether a laptop is priced unusually well (a "deal") relative
    to comparable machines (same CPU/GPU power tier and RAM size). Returns a
    dict {(cpu_tier, gpu_tier, ram_band): median_price} plus the global median
    for tiers with too few comparable rows to be trusted.
    """
    from collections import defaultdict

    bands = defaultdict(list)
    for lp in laptops:
        price = lp["Price_NPR"]
        if price <= 0:
            continue
        cpu = max(1, cpu_tier(lp["CPU_Model"] or ""))
        gpu = max(1, gpu_tier(lp["GPU_Model"] or ""))
        ram = lp["RAM_GB"]
        if ram >= 32:
            band = 32
        elif ram >= 16:
            band = 16
        elif ram >= 8:
            band = 8
        else:
            band = 4
        bands[(cpu, gpu, band)].append(price)

    all_prices = [p for prices in bands.values() for p in prices]
    global_median = sorted(all_prices)[len(all_prices) // 2] if all_prices else 0

    medians = {}
    for key, prices in bands.items():
        prices_sorted = sorted(prices)
        medians[key] = prices_sorted[len(prices_sorted) // 2]

    return medians, global_median


def _classify_deal(laptop, deal_context):
    """Return a short deal label + flag for a laptop vs comparable machines.

    Returns (is_deal: bool, tier: "great"|"good"|"fair"|"premium", note: str).
    """
    medians, global_median = deal_context
    price = laptop["Price_NPR"]
    if price <= 0 or global_median <= 0:
        return False, "fair", ""

    cpu = max(1, cpu_tier(laptop["CPU_Model"] or ""))
    gpu = max(1, gpu_tier(laptop["GPU_Model"] or ""))
    ram = laptop["RAM_GB"]
    band = 32 if ram >= 32 else 16 if ram >= 16 else 8 if ram >= 8 else 4

    key = (cpu, gpu, band)
    comparator = medians.get(key, global_median)
    ratio = price / comparator

    if ratio <= 0.85:
        return True, "great", "Priced well below comparable models"
    if ratio <= 0.97:
        return True, "good", "Competitively priced for its specs"
    if ratio <= 1.1:
        return False, "fair", ""
    return False, "premium", "Priced at a premium for its specs"


def recommend(user_input, top_n=5, data_path=None):
    rows = load_data(data_path)
    laptops = preprocess(rows)

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
        "min_cpu_tier": int(user_input.get("min_cpu_tier", 0) or 0),
        "min_gpu_tier": int(user_input.get("min_gpu_tier", 0) or 0),
        "brand": user_input.get("brand", ""),
        "storage_type": user_input.get("storage_type", ""),
        "min_screen": float(user_input.get("min_screen", 0) or 0),
        "touchscreen": user_input.get("touchscreen", False),
        "dedicated_gpu": user_input.get("dedicated_gpu", False),
    }

    scored = []
    for laptop in laptops:
        if budget > 0 and laptop["Price_NPR"] > budget * 1.5:
            continue
        if user["min_ram"] > 0 and laptop["RAM_GB"] < user["min_ram"] * 0.5:
            continue
        if user["storage_type"] and user["storage_type"].lower() not in "any":
            lt_st = laptop["Storage_Type"].lower()
            if lt_st != "unknown" and user["storage_type"].lower() not in lt_st and lt_st not in user["storage_type"].lower():
                continue
        if user["min_screen"] > 0 and laptop["Screen_Size_Inches"] > 0 and laptop["Screen_Size_Inches"] < user["min_screen"]:
            continue
        if user["touchscreen"] and laptop["Touchscreen"] == 0:
            continue
        if user["dedicated_gpu"]:
            gpu_model_lower = laptop["GPU_Model"].lower()
            if "integrated" in gpu_model_lower or laptop["GPU_Brand"].lower() in ("intel", "unknown"):
                continue

        score, reasons, penalties = score_laptop(laptop, user)
        scored.append({
            "laptop": laptop,
            "score": round(score, 2),
            "reasons": reasons,
            "penalties": penalties,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    deal_context = _deal_context(laptops)

    def _annotated(item):
        is_deal, deal_tier, deal_note = _classify_deal(item["laptop"], deal_context)
        return {
            "laptop": format_laptop(item["laptop"]),
            "score": item["score"],
            "reasons": item["reasons"],
            "penalties": item["penalties"],
            "deal": {
                "is_deal": is_deal,
                "tier": deal_tier,
                "note": deal_note,
            },
        }

    if not scored:
        closest = sorted(laptops, key=lambda x: x["Price_NPR"])
        if budget > 0:
            below = [l for l in closest if l["Price_NPR"] <= budget]
            above = [l for l in closest if l["Price_NPR"] > budget]
            fallback_pool = below[-5:] if below else above[:5]
        else:
            fallback_pool = closest[:5]

        result = []
        for laptop in fallback_pool:
            score, reasons, penalties = score_laptop(laptop, user)
            reasons.insert(0, "Closest alternative (no exact match found)")
            result.append(_annotated({
                "laptop": laptop,
                "score": round(score, 2),
                "reasons": reasons,
                "penalties": penalties,
            }))
        return {
            "status": "no_exact_match",
            "message": "No laptops exactly match your criteria. Showing closest alternatives.",
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
        "message": f"Found {len(scored)} matching laptops. Showing top {len(result)}.",
        "recommendations": result,
        "user_query": {
            "budget": budget,
            "purpose": purpose_raw,
            "purpose_labels": list(purpose_labels),
        },
    }


def get_dataset_stats(data_path=None):
    from collections import defaultdict
    rows = load_data(data_path)
    laptops = preprocess(rows)

    brands = defaultdict(int)
    purposes = defaultdict(int)
    for lt in laptops:
        brands[lt["Brand"]] += 1
        for p in lt["Purpose_Labels"]:
            purposes[p] += 1

    prices = [lt["Price_NPR"] for lt in laptops if lt["Price_NPR"] > 0]

    return {
        "total_laptops": len(laptops),
        "brands": dict(sorted(brands.items(), key=lambda x: -x[1])),
        "purpose_distribution": dict(sorted(purposes.items(), key=lambda x: -x[1])),
        "price_range": {
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0,
            "avg": sum(prices) / len(prices) if prices else 0,
        },
    }


def get_available_brands(data_path=None):
    rows = load_data(data_path)
    laptops = preprocess(rows)
    return sorted(set(lt["Brand"] for lt in laptops))


def get_insights(data_path=None):
    """Aggregated dataset insights for frontend visualization dashboards."""
    from collections import defaultdict

    laptops = preprocess(load_data(data_path))
    total = len(laptops)
    prices = [lt["Price_NPR"] for lt in laptops if lt["Price_NPR"] > 0]

    # Price histogram: NPR 10K buckets up to 200K, then one open-ended bucket.
    price_histogram = []
    step = 10000
    for start in range(0, 200000, step):
        end = start + step
        price_histogram.append({
            "bucket": f"{start // 1000}K-{end // 1000}K",
            "count": sum(1 for p in prices if start <= p < end),
        })
    price_histogram.append({
        "bucket": "200K+",
        "count": sum(1 for p in prices if p >= 200000),
    })
    while price_histogram and price_histogram[0]["count"] == 0:
        price_histogram.pop(0)

    brand_counts = defaultdict(int)
    purpose_counts = defaultdict(int)
    cpu_counts = defaultdict(int)
    gpu_counts = defaultdict(int)
    storage_counts = defaultdict(int)
    ram_groups = defaultdict(list)

    for lt in laptops:
        brand_counts[lt["Brand"]] += 1
        for p in lt["Purpose_Labels"]:
            purpose_counts[p] += 1
        cpu_counts[cpu_tier(lt["CPU_Model"])] += 1
        gpu_counts[gpu_tier(lt["GPU_Model"])] += 1
        storage_counts[lt["Storage_Type"]] += 1
        if lt["RAM_GB"] > 0:
            ram_groups[int(lt["RAM_GB"])].append(lt["Price_NPR"])

    ram_vs_price = []
    for ram in sorted(ram_groups):
        vals = ram_groups[ram]
        if len(vals) < 20:
            continue  # skip rare configs (e.g. 18GB x1) so the chart stays readable
        ram_vs_price.append({
            "ram_gb": ram,
            "avg_price": round(sum(vals) / len(vals)),
            "count": len(vals),
        })

    return {
        "total_laptops": total,
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
        "ram_vs_price": ram_vs_price,
        "cpu_tier_distribution": [
            {"tier": t, "count": cpu_counts.get(t, 0)} for t in range(1, 7)
        ],
        "gpu_tier_distribution": [
            {"tier": t, "count": gpu_counts.get(t, 0)} for t in range(1, 7)
        ],
        "storage_type_distribution": [
            {"storage_type": s, "count": c}
            for s, c in sorted(storage_counts.items(), key=lambda x: -x[1])
        ],
    }


if __name__ == "__main__":
    test_cases = [
        {"budget": "100000", "purpose": "gaming", "min_ram": 16, "min_storage": 512, "storage_type": "SSD"},
        {"budget": "80000", "purpose": "programming", "min_ram": 8},
        {"budget": "50000", "purpose": "student"},
        {"budget": "200000", "purpose": "video editing and graphic design", "min_ram": 32, "min_storage": 1000},
        {"budget": "30000", "purpose": "office work"},
        {"budget": "150000", "purpose": "machine learning and AI", "brand": "Dell"},
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"\nTEST {i}: Budget={tc['budget']}, Purpose={tc['purpose']}")
        result = recommend(tc, top_n=3)
        print(f"Status: {result['status']} | {result['message']}")
        for j, rec in enumerate(result["recommendations"], 1):
            lt = rec["laptop"]
            print(f"  #{j} [{rec['score']}pts] {lt['brand']} {lt['cpu_model']}")
            print(f"     GPU: {lt['gpu_model']} | RAM: {lt['ram_gb']:.0f}GB | Storage: {lt['storage_gb']:.0f}GB {lt['storage_type']}")
            print(f"     Price: NPR {lt['price_npr']:,.0f}")
            for r in rec["reasons"][:3]:
                print(f"     + {r}")
