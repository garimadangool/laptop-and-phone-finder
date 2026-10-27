"""Clean the raw Smartprix mobile dataset into phones_ml_ready.csv.

Reads: data/Analysed and Cleaned Mobiles Dataset from Smartprix.csv
Writes: data/phones_ml_ready.csv

Only rows with Brand, Product_Name, Current_Price, RAM_GB, Storage_GB,
and Chipset are kept. Everything else is parsed into clean columns.
"""

import csv
import re
import os

RAW_PATH = os.path.join(
    os.path.dirname(__file__), "..",
    "Analysed and Cleaned Mobiles Dataset from Smartprix.csv",
)
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "phones_ml_ready.csv")

FIELDNAMES = [
    "Brand", "Product_Name", "Chipset", "GPU", "RAM_GB", "Storage_GB",
    "Storage_Type", "Display_Size_Inches", "Display_Type", "Battery_mAh",
    "Fast_Charging_W", "Rear_Camera_MP", "Front_Camera_MP", "Has_OIS",
    "Has_5G", "Has_NFC", "Has_Fingerprint", "Weight_Grams", "OS",
    "Price_NPR", "Original_Price", "Purpose",
]


# ── helpers ──────────────────────────────────────────────────────────────

def safe_float(val, default=0.0):
    try:
        v = float(str(val).replace(",", "").strip())
        return v if v > 0 else default
    except (ValueError, TypeError):
        return default


def parse_fast_charging(val):
    if not val or val.strip().lower() in ("no", ""):
        return 0
    m = re.search(r"(\d+)\s*[Ww]", val)
    return int(m.group(1)) if m else 0


def parse_camera_mp(val):
    if not val:
        return 0
    m = re.search(r"(\d+)\s*[Mm][Pp]", val)
    return int(m.group(1)) if m else 0


def parse_battery_mah(val):
    if not val:
        return 0
    m = re.search(r"(\d+)\s*m[Aa][Hh]", val)
    if m:
        return int(m.group(1))
    try:
        v = int(float(val.strip()))
        return v if 200 <= v <= 30000 else 0
    except (ValueError, TypeError):
        return 0


def normalize_os(val):
    if not val:
        return "Unknown"
    v = val.lower()
    if "android" in v:
        return "Android"
    if "ios" in v:
        return "iOS"
    if "harmonyos" in v or "hongmeng" in v:
        return "HarmonyOS"
    if "windows" in v:
        return "Windows"
    if "symbian" in v:
        return "Symbian"
    if "blackberry" in v:
        return "BlackBerry"
    if "kaios" in v:
        return "KaiOS"
    return "Other"


def classify_display(val):
    if not val:
        return "Unknown"
    v = val.lower()
    if "amoled" in v or "oled" in v or "super amoled" in v:
        return "AMOLED"
    if "ips" in v or "lcd" in v:
        return "IPS-LCD"
    if "tft" in v:
        return "TFT"
    return "Other"


def is_yes(val):
    if not val:
        return "No"
    return "Yes" if val.strip().lower().startswith("yes") else "No"


def has_ois(val):
    if not val:
        return "No"
    return "Yes" if "ois" in val.lower() else "No"


def classify_chipset_family(chipset):
    c = chipset.lower()
    if "snapdragon" in c or "qualcomm" in c:
        return "Qualcomm"
    if "mediatek" in c or "helio" in c or "dimensity" in c:
        return "MediaTek"
    if "unisoc" in c or "Spreadtrum" in c:
        return "Unisoc"
    if "exynos" in c:
        return "Samsung"
    if "tensor" in c:
        return "Google"
    if "kirin" in c:
        return "Huawei"
    if "a1" in c and ("apple" in c or "bionic" in c):
        return "Apple"
    if "m1" in c and "apple" in c:
        return "Apple"
    return "Other"


def classify_chipset_tier(chipset):
    """Rate chipset performance 1-6 based on known model names."""
    c = chipset.lower()

    tier6 = [
        "snapdragon 8 elite", "snapdragon 8 gen3", "snapdragon 8 gen2",
        "snapdragon 8+ gen1", "snapdragon 888", "snapdragon 870",
        "dimensity 9300", "dimensity 9200", "dimensity 9000",
        "a18 pro", "a18", "a17 pro", "a17", "a16 pro", "a16",
        "a20 pro", "a20", "a19 pro", "a19",
        "exynos 2400", "exynos 2200", "tensor g4", "tensor g3",
        "kirin 9", "snapdragon 8s gen3",
    ]
    tier5 = [
        "snapdragon 7+ gen3", "snapdragon 7+ gen2", "snapdragon 7 gen3",
        "snapdragon 7s gen3", "snapdragon 7 gen2",
        "dimensity 8300", "dimensity 8200", "dimensity 8100",
        "dimensity 7200", "dimensity 7300",
        "tensor g2", "exynos 1480", "exynos 1380",
        "kirin 8",
        "a15",
    ]
    tier4 = [
        "snapdragon 720g", "snapdragon 730g", "snapdragon 732g",
        "snapdragon 750g", "snapdragon 765g", "snapdragon 768g",
        "snapdragon 778g", "snapdragon 780g", "snapdragon 6 gen1",
        "snapdragon 6s gen3", "snapdragon 695", "snapdragon 685",
        "snapdragon 680",
        "dimensity 7050", "dimensity 7025", "dimensity 7020",
        "dimensity 7000", "dimensity 6080", "dimensity 6020",
        "dimensity 6100", "helio g99", "helio g96", "helio g95",
        "exynos 1280", "exynos 1080",
        "a14", "a13",
    ]
    tier3 = [
        "snapdragon 665", "snapdragon 662", "snapdragon 660",
        "snapdragon 650", "snapdragon 652",
        "dimensity 800", "dimensity 810", "dimensity 820",
        "dimensity 700", "dimensity 6300", "dimensity 6125",
        "helio g88", "helio g85", "helio g80", "helio g70",
        "helio g35", "helio g25",
        "exynos 9611", "exynos 9610",
        "kirin 7",
        "a12", "a11", "a10",
    ]
    tier2 = [
        "snapdragon 460", "snapdragon 450", "snapdragon 439",
        "snapdragon 429", "snapdragon 410",
        "helio a25", "helio a22", "helio a20",
        "unisoc t618", "unisoc t616", "unisoc t612", "unisoc t610",
        "unisoc t606", "unisoc t603",
        "exynos 850", "exynos 7904",
        "a9", "a8", "a7", "a6",
    ]

    for tier_map, tier_val in [(tier6, 6), (tier5, 5), (tier4, 4), (tier3, 3), (tier2, 2)]:
        for pat in tier_map:
            if pat in c:
                return tier_val
    return 1


def derive_purposes(phone):
    labels = []
    c = phone["Chipset"].lower()
    ram = phone["RAM_GB"]
    price = phone["Price_NPR"]
    cam = phone["Rear_Camera_MP"]
    batt = phone["Battery_mAh"]
    tier = phone["Chipset_Tier"]

    if tier >= 5:
        labels.append("Fast Performance")
        labels.append("Gaming")
    elif tier >= 4:
        labels.append("Fast Performance")

    if cam >= 50 or phone["Has_OIS"] == "Yes":
        labels.append("Camera")

    if price <= 15000:
        labels.append("Student")
    elif price <= 30000:
        labels.append("General Use")
    elif price <= 60000:
        labels.append("General Use")

    if ram >= 8:
        labels.append("Heavy Multitasking")

    if batt >= 5500:
        labels.append("Battery Life")

    if tier >= 4 and ram >= 6:
        labels.append("General Use")

    if not labels:
        labels.append("General Use")

    seen = set()
    unique = []
    for l in labels:
        if l not in seen:
            seen.add(l)
            unique.append(l)
    return unique


# ── main ─────────────────────────────────────────────────────────────────

def main():
    with open(RAW_PATH, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    cleaned = []
    skipped = 0

    for r in rows:
        brand = r.get("Brand", "").strip()
        product = r.get("Product_Name", "").strip()
        chipset = r.get("Chipset", "").strip()
        price = safe_float(r.get("Current_Price", "0"))
        ram = safe_float(r.get("RAM_GB", "0"))
        storage = safe_float(r.get("Storage_GB", "0"))

        if not brand or not chipset or price <= 500 or ram <= 0 or storage <= 0:
            skipped += 1
            continue

        gpu = r.get("GPU", "").strip() or "Unknown"
        batt = parse_battery_mah(r.get("Battery_Size", "") or r.get("Battery_Capacity_mAh", ""))
        orig_price = safe_float(r.get("Original_Price", "0"))

        phone = {
            "Brand": brand,
            "Product_Name": product,
            "Chipset": chipset,
            "GPU": gpu,
            "RAM_GB": ram,
            "Storage_GB": storage,
            "Storage_Type": (r.get("Storage_Type", "") or "").strip() or "Unknown",
            "Display_Size_Inches": safe_float(r.get("Display_Size_Inches", "0")),
            "Display_Type": classify_display(r.get("Display_Type", "")),
            "Battery_mAh": batt,
            "Fast_Charging_W": parse_fast_charging(r.get("Fast_Charging", "")),
            "Rear_Camera_MP": parse_camera_mp(r.get("Rear_Camera", "")),
            "Front_Camera_MP": parse_camera_mp(r.get("Front_Camera", "")),
            "Has_OIS": has_ois(r.get("Rear_Camera", "")),
            "Has_5G": is_yes(r.get("Has_5G", "")),
            "Has_NFC": is_yes(r.get("NFC", "")),
            "Has_Fingerprint": is_yes(r.get("Fingerprint_Sensor", "")),
            "Weight_Grams": safe_float(r.get("Weight_Grams", "0")),
            "OS": normalize_os(r.get("Operating_System", "")),
            "Price_NPR": price,
            "Original_Price": orig_price,
        }

        phone["Chipset_Family"] = classify_chipset_family(chipset)
        phone["Chipset_Tier"] = classify_chipset_tier(chipset)

        purposes = derive_purposes(phone)
        phone["Purpose"] = ", ".join(purposes)

        cleaned.append(phone)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    out_fields = [
        "Brand", "Product_Name", "Chipset", "Chipset_Family", "Chipset_Tier",
        "GPU", "RAM_GB", "Storage_GB", "Storage_Type", "Display_Size_Inches",
        "Display_Type", "Battery_mAh", "Fast_Charging_W", "Rear_Camera_MP",
        "Front_Camera_MP", "Has_OIS", "Has_5G", "Has_NFC", "Has_Fingerprint",
        "Weight_Grams", "OS", "Price_NPR", "Original_Price", "Purpose",
    ]

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"Raw rows: {len(rows)}")
    print(f"Cleaned: {len(cleaned)}, Skipped: {skipped}")
    print(f"Written to: {OUT_PATH}")

    brands = {}
    purposes = {}
    families = {}
    tiers = {}
    for p in cleaned:
        brands[p["Brand"]] = brands.get(p["Brand"], 0) + 1
        for pl in p["Purpose"].split(", "):
            if pl:
                purposes[pl] = purposes.get(pl, 0) + 1
        families[p["Chipset_Family"]] = families.get(p["Chipset_Family"], 0) + 1
        tiers[p["Chipset_Tier"]] = tiers.get(p["Chipset_Tier"], 0) + 1

    print(f"\nBrands ({len(brands)}): {dict(sorted(brands.items(), key=lambda x:-x[1])[:10])}")
    print(f"Purposes: {dict(sorted(purposes.items(), key=lambda x:-x[1]))}")
    print(f"Chipset families: {dict(sorted(families.items(), key=lambda x:-x[1]))}")
    print(f"Chipset tiers: {dict(sorted(tiers.items()))}")
    prices = [p["Price_NPR"] for p in cleaned]
    print(f"Price: min={min(prices):.0f}, max={max(prices):.0f}, avg={sum(prices)/len(prices):.0f}")


if __name__ == "__main__":
    main()
