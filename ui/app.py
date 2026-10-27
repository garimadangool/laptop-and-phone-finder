import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from model.recommend import (
    recommend,
    get_dataset_stats,
    get_available_brands,
    ALL_PURPOSE_LABELS,
    parse_user_budget,
)

st.set_page_config(
    page_title="LaptopNepal — Find Your Perfect Laptop",
    page_icon="💻",
    layout="centered",
)

css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


PURPOSE_OPTIONS = [
    ("Gaming", "🎮"),
    ("Programming", "💻"),
    ("Student", "📚"),
    ("Creative Work", "🎨"),
    ("Office / Business", "💼"),
    ("Everyday Use", "🏠"),
]

BRAND_COLORS = {
    "HP": "#0096D6",
    "Lenovo": "#E2231A",
    "ASUS": "#00539B",
    "Dell": "#007DB8",
    "MSI": "#FF0000",
    "Acer": "#83B81A",
    "Apple": "#555555",
    "Samsung": "#1428A0",
    "Toshiba": "#FF6600",
    "Microsoft": "#737373",
    "Razer": "#44D62C",
    "Gigabyte": "#F06D00",
    "Huawei": "#CF0A2C",
    "Infinix": "#00B5D8",
    "Realme": "#F5C518",
}
DEFAULT_BRAND_COLOR = "#64748b"

LAPTOP_SVG = (
    '<svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="30" y="10" width="140" height="85" rx="6" fill="{bg}" stroke="#cbd5e1" stroke-width="2"/>'
    '<rect x="38" y="18" width="124" height="69" rx="3" fill="#f1f5f9"/>'
    '<rect x="60" y="95" width="80" height="6" rx="3" fill="{bg}" stroke="#cbd5e1" stroke-width="1.5"/>'
    '<rect x="20" y="101" width="160" height="8" rx="4" fill="{bg}" stroke="#cbd5e1" stroke-width="1.5"/>'
    '<circle cx="100" cy="52" r="12" fill="{accent}" opacity="0.25"/>'
    '<text x="100" y="57" text-anchor="middle" font-size="11" font-weight="700" fill="{accent}" font-family="Inter,sans-serif">{brand_letter}</text>'
    '</svg>'
)

HERO_LAPTOP_SVG = (
    '<svg viewBox="0 0 280 200" xmlns="http://www.w3.org/2000/svg">'
    '<defs><linearGradient id="screen" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" style="stop-color:#dbeafe"/><stop offset="100%" style="stop-color:#ede9fe"/></linearGradient></defs>'
    '<rect x="40" y="15" width="200" height="120" rx="8" fill="#1e293b" stroke="#475569" stroke-width="2"/>'
    '<rect x="48" y="23" width="184" height="104" rx="4" fill="url(#screen)"/>'
    '<text x="140" y="65" text-anchor="middle" font-size="28" font-weight="900" fill="#2563eb" font-family="Inter,sans-serif">💻</text>'
    '<text x="140" y="90" text-anchor="middle" font-size="10" font-weight="600" fill="#64748b" font-family="Inter,sans-serif">5,284 laptops</text>'
    '<rect x="80" y="135" width="120" height="8" rx="4" fill="#475569"/>'
    '<rect x="30" y="143" width="220" height="10" rx="5" fill="#334155" stroke="#475569" stroke-width="1.5"/>'
    '</svg>'
)


def get_brand_color(brand):
    for k, v in BRAND_COLORS.items():
        if k.lower() in brand.lower():
            return v
    return DEFAULT_BRAND_COLOR


def render_purpose_cards(selected_purpose):
    cards = ""
    for label, icon in PURPOSE_OPTIONS:
        sel = "selected" if selected_purpose == label else ""
        cards += f"""
        <div class="purpose-card {sel}">
            <span class="purpose-icon">{icon}</span>
            <span class="purpose-label">{label}</span>
        </div>"""
    return f'<div class="purpose-grid">{cards}</div>'


def render_laptop_card(rank, rec):
    lt = rec["laptop"]
    score = rec["score"]
    reasons = rec["reasons"]
    penalties = rec["penalties"]
    brand = lt["brand"]

    score_label = (
        "Excellent" if score >= 90
        else "Great" if score >= 80
        else "Good" if score >= 70
        else "Fair" if score >= 60
        else "Basic"
    )

    top_class = "top-match" if rank <= 3 else ""
    top_badge = '<div class="top-badge">★ Best Match</div>' if rank == 1 else ""

    brand_color = get_brand_color(brand)
    brand_letter = brand[0].upper() if brand else "L"
    laptop_svg = LAPTOP_SVG.format(bg=brand_color, accent=brand_color, brand_letter=brand_letter)

    reasons_html = "".join(f'<span class="reason-tag">✓ {r}</span>' for r in reasons)
    penalties_html = "".join(f'<span class="penalty-tag">✗ {p}</span>' for p in penalties)

    specs = [
        ("RAM", f"{lt['ram_gb']:.0f} GB"),
        ("Storage", f'{lt["storage_gb"]:.0f} GB {lt["storage_type"]}' if lt["storage_gb"] > 0 else None),
        ("GPU", lt['gpu_model'][:22] if lt['gpu_model'] and lt['gpu_model'] != "Integrated" else "Integrated"),
        ("CPU", f'{lt["cpu_brand"]} Tier {lt["cpu_tier"]}/6'),
        ("OS", lt['os'] if lt['os'] != "Unknown" else None),
        ("Screen", f'{lt["screen_size"]:.1f}"' if lt["screen_size"] > 0 else None),
        ("Weight", f"{lt['weight_kg']:.1f} kg" if lt["weight_kg"] > 0 else None),
        ("Touchscreen", "Yes" if lt["touchscreen"] else None),
    ]

    spec_tags = ""
    shown = 0
    for label, value in specs:
        if value is None or shown >= 6:
            continue
        spec_tags += f'<span class="spec-tag"><span class="spec-key">{label}</span> <span class="spec-val">{value}</span></span>'
        shown += 1

    return f"""
    <div class="rec-card {top_class}">
        {top_badge}
        <div class="rec-image">
            <div class="brand-badge">{brand}</div>
            {laptop_svg}
        </div>
        <div class="rec-body">
            <div class="rec-top-row">
                <div class="rec-score"><span class="score-dot"></span> {score:.0f}/100 · {score_label}</div>
                <div class="rec-price-block">
                    <div class="rec-price">NPR {lt['price_npr']:,.0f}</div>
                    <div class="rec-price-label">Best price in Nepal</div>
                </div>
            </div>
            <div class="rec-name">{brand} — {lt['cpu_model']}</div>
            <div class="rec-specs">{spec_tags}</div>
            <div class="rec-tags">{reasons_html}{penalties_html}</div>
        </div>
    </div>
    """


# =====================================================================
# SESSION STATE
# =====================================================================
if "purpose" not in st.session_state:
    st.session_state.purpose = "Gaming"
if "budget_text" not in st.session_state:
    st.session_state.budget_text = ""
if "results" not in st.session_state:
    st.session_state.results = None


# =====================================================================
# HERO
# =====================================================================
st.markdown(
    '<div class="hero-section">'
    '<div class="hero-content">'
    '<span class="hero-tag">Smart Laptop Finder for Nepal</span>'
    '<h1 class="hero-title">Find Your<br>Perfect Laptop</h1>'
    '<p class="hero-subtitle">Tell us what you need and your budget. We\'ll match you with the best laptops — powered by smart recommendations.</p>'
    '</div>'
    '<div class="hero-image">'
    f'{HERO_LAPTOP_SVG}'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

# =====================================================================
# STATS
# =====================================================================
stats = get_dataset_stats()
st.markdown(
    '<div class="stats-bar">'
    f'<div class="stat-item"><span class="stat-icon">💻</span><div class="stat-number">{stats["total_laptops"]:,}</div><div class="stat-label">Laptops</div></div>'
    f'<div class="stat-item"><span class="stat-icon">🏷️</span><div class="stat-number">{len(stats["brands"])}</div><div class="stat-label">Brands</div></div>'
    f'<div class="stat-item"><span class="stat-icon">🎯</span><div class="stat-number">{len(stats["purpose_distribution"])}</div><div class="stat-label">Categories</div></div>'
    f'<div class="stat-item"><span class="stat-icon">💰</span><div class="stat-number">NPR {stats["price_range"]["max"]/1000:.0f}K</div><div class="stat-label">Max Price</div></div>'
    '</div>',
    unsafe_allow_html=True,
)


# =====================================================================
# STEP 1 — PURPOSE
# =====================================================================
st.markdown(
    '<div class="section-header">'
    '<span class="section-number">1</span>'
    '<h2 class="section-title">What are you looking for?</h2>'
    '</div>'
    '<p class="section-hint">Pick the category that best describes how you\'ll use the laptop.</p>',
    unsafe_allow_html=True,
)

purpose_cols = st.columns(len(PURPOSE_OPTIONS))
for i, (label, icon) in enumerate(PURPOSE_OPTIONS):
    with purpose_cols[i]:
        if st.button(f"{icon} {label}", key=f"p_{label}", use_container_width=True):
            st.session_state.purpose = label
            st.session_state.results = None
            st.rerun()

st.markdown(render_purpose_cards(st.session_state.purpose), unsafe_allow_html=True)


# =====================================================================
# STEP 2 — BUDGET
# =====================================================================
st.markdown(
    '<div class="section-header">'
    '<span class="section-number">2</span>'
    '<h2 class="section-title">What\'s your budget?</h2>'
    '</div>'
    '<p class="section-hint">Enter how much you want to spend. We use Nepali Rupees (NPR).</p>',
    unsafe_allow_html=True,
)

budget_text = st.text_input(
    "Budget",
    value=st.session_state.budget_text,
    placeholder="e.g. 100000, 1.5 lakh, 80k",
    label_visibility="collapsed",
)
st.session_state.budget_text = budget_text

chip_cols = st.columns(6)
chip_values = ["30000", "50000", "80000", "1 lakh", "1.5 lakh", "2 lakh"]
chip_labels = ["30K", "50K", "80K", "1 Lakh", "1.5 Lakh", "2 Lakh+"]
for i, (val, lbl) in enumerate(zip(chip_values, chip_labels)):
    with chip_cols[i]:
        if st.button(lbl, key=f"chip_{val}", use_container_width=True):
            st.session_state.budget_text = val
            st.session_state.results = None
            st.rerun()


# =====================================================================
# STEP 3 — OPTIONAL SPECS
# =====================================================================
with st.expander("**Step 3** · What matters most to you? (optional)", expanded=False):
    s1, s2 = st.columns(2)
    with s1:
        min_ram = st.number_input("Minimum RAM (GB)", min_value=0, max_value=128, value=0, step=2, help="0 = any RAM")
    with s2:
        min_storage = st.number_input("Minimum Storage (GB)", min_value=0, max_value=4000, value=0, step=128, help="0 = any storage")

    s3, s4 = st.columns(2)
    with s3:
        storage_type = st.selectbox("Storage Type", ["Any", "SSD", "HDD"], index=0)
    with s4:
        brand = st.selectbox("Brand", ["Any"] + get_available_brands(), index=0)

    s5, s6 = st.columns(2)
    with s5:
        min_screen = st.number_input('Min Screen (")', min_value=0.0, max_value=20.0, value=0.0, step=0.1, help="0 = any size")
    with s6:
        touchscreen = st.checkbox("Touchscreen required")

    st.markdown("**Advanced**")
    a1, a2 = st.columns(2)
    with a1:
        dedicated_gpu = st.checkbox("Dedicated GPU only", help="Exclude integrated graphics")
    with a2:
        min_cpu_tier = st.slider("Min CPU Power", min_value=0, max_value=6, value=0, help="0 = any, 6 = workstation class")

    min_gpu_tier = st.slider("Min GPU Power", min_value=0, max_value=6, value=0, help="0 = any, 6 = high-end gaming")

    top_n = st.slider("Number of results", min_value=1, max_value=15, value=5)


# =====================================================================
# FIND + RESULTS
# =====================================================================
st.markdown("---")

find_c1, find_c2, find_c3 = st.columns([1, 2, 1])
with find_c2:
    find_clicked = st.button("🔍  Find My Perfect Laptop", use_container_width=True, type="primary")

if find_clicked:
    st.session_state.results = None
    if not budget_text.strip():
        st.error("Please enter a budget above.")
    else:
        parsed = parse_user_budget(budget_text)
        if parsed is None:
            st.error("Could not understand your budget. Try `100000` or `1.5 lakh`.")
        elif parsed <= 0:
            st.error("Budget must be a positive number.")
        else:
            user_input = {
                "budget": budget_text,
                "purpose": st.session_state.purpose,
                "min_ram": min_ram if "min_ram" in dir() else 0,
                "min_storage": min_storage if "min_storage" in dir() else 0,
                "storage_type": storage_type if "storage_type" in dir() and storage_type != "Any" else "",
                "brand": brand if "brand" in dir() and brand != "Any" else "",
                "min_screen": min_screen if "min_screen" in dir() else 0.0,
                "touchscreen": touchscreen if "touchscreen" in dir() else False,
                "dedicated_gpu": dedicated_gpu if "dedicated_gpu" in dir() else False,
                "min_cpu_tier": min_cpu_tier if "min_cpu_tier" in dir() else 0,
                "min_gpu_tier": min_gpu_tier if "min_gpu_tier" in dir() else 0,
                "top_n": top_n if "top_n" in dir() else 5,
            }
            try:
                with st.spinner("Finding the best laptops for you..."):
                    result = recommend(user_input, top_n=top_n)
                st.session_state.results = result
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.info("Try different parameters and search again.")


if st.session_state.results:
    result = st.session_state.results
    parsed_budget = parse_user_budget(budget_text) if budget_text.strip() else 0

    st.markdown(
        f'<div class="results-header">'
        f'<h3>🎯 Recommended for You</h3>'
        f'<div class="results-meta">{result["message"]} &nbsp;·&nbsp; Budget: NPR {parsed_budget:,.0f} &nbsp;·&nbsp; Purpose: {st.session_state.purpose}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not result["recommendations"]:
        st.markdown(
            '<div class="info-box"><p>No laptops matched your exact criteria. Try relaxing some filters or adjusting your budget.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        for i, rec in enumerate(result["recommendations"], 1):
            st.markdown(render_laptop_card(i, rec), unsafe_allow_html=True)

        st.markdown(
            '<div class="info-box"><p>💡 Want different results? Change your preferences above and hit <strong>Find My Perfect Laptop</strong> again.</p></div>',
            unsafe_allow_html=True,
        )
