import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from model.recommend import load_data, preprocess, cpu_tier, gpu_tier, CPU_TIERS, GPU_TIERS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(OUT_DIR, exist_ok=True)

rows = preprocess(load_data())
prices = [r["Price_NPR"] for r in rows if r["Price_NPR"] > 0]
brands = [r["Brand"] for r in rows]
rams = [r["RAM_GB"] for r in rows if r["RAM_GB"] > 0]
storages = [r["Storage_GB"] for r in rows if r["Storage_GB"] > 0]
screens = [r["Screen_Size_Inches"] for r in rows if r["Screen_Size_Inches"] > 0]
weights = [r["Weight_KG"] for r in rows if r["Weight_KG"] > 0]
cpu_tiers = [cpu_tier(r["CPU_Model"]) for r in rows]
gpu_tiers = [gpu_tier(r["GPU_Model"]) for r in rows]

purpose_labels = {}
for r in rows:
    for p in r["Purpose_Labels"]:
        purpose_labels[p] = purpose_labels.get(p, 0) + 1

brand_counts = {}
for b in brands:
    brand_counts[b] = brand_counts.get(b, 0) + 1
top_brands = sorted(brand_counts.items(), key=lambda x: -x[1])[:12]

plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#e0e0e0",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#e0e0e0",
    "ytick.color": "#e0e0e0",
    "figure.dpi": 150,
    "font.size": 10,
})

ACCENT = "#0f3460"
HIGHLIGHT = "#e94560"
COLORS = ["#e94560", "#0f3460", "#533483", "#00b4d8", "#e76f51",
          "#2a9d8f", "#f4a261", "#264653", "#e9c46a", "#d62828",
          "#023e8a", "#0077b6"]


def fmt_npr(x, _):
    if x >= 100000:
        return f"{x/100000:.1f}L"
    return f"{x/1000:.0f}K"


def chart_price_distribution():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(prices, bins=60, color=HIGHLIGHT, edgecolor="#1a1a2e", alpha=0.85)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(fmt_npr))
    ax.set_xlabel("Price (NPR)")
    ax.set_ylabel("Number of Laptops")
    ax.set_title("Laptop Price Distribution", fontsize=14, fontweight="bold", pad=15)
    median_p = np.median(prices)
    ax.axvline(median_p, color="#e9c46a", linestyle="--", linewidth=1.5, label=f"Median: NPR {median_p:,.0f}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "01_price_distribution.png"))
    plt.close()
    print("  01_price_distribution.png")


def chart_brand_market_share():
    fig, ax = plt.subplots(figsize=(10, 6))
    names = [b[0] for b in top_brands]
    counts = [b[1] for b in top_brands]
    bars = ax.barh(names[::-1], counts[::-1], color=COLORS[:len(names)])
    ax.set_xlabel("Number of Laptops")
    ax.set_title("Top 12 Brands by Number of Laptops", fontsize=14, fontweight="bold", pad=15)
    for bar, val in zip(bars, counts[::-1]):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "02_brand_market_share.png"))
    plt.close()
    print("  02_brand_market_share.png")


def chart_price_by_brand():
    fig, ax = plt.subplots(figsize=(10, 6))
    brand_prices = {}
    for r in rows:
        if r["Price_NPR"] > 0:
            brand_prices.setdefault(r["Brand"], []).append(r["Price_NPR"])
    box_data = []
    box_labels = []
    for brand, _ in top_brands:
        if brand in brand_prices and len(brand_prices[brand]) >= 3:
            box_data.append(brand_prices[brand])
            box_labels.append(brand)
    bp = ax.boxplot(box_data, patch_artist=True, vert=True,
                    medianprops=dict(color="#e9c46a", linewidth=2))
    ax.set_xticklabels(box_labels, rotation=45, ha="right")
    for patch, color in zip(bp["boxes"], COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_npr))
    ax.set_ylabel("Price (NPR)")
    ax.set_title("Price Distribution by Brand", fontsize=14, fontweight="bold", pad=15)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "03_price_by_brand.png"))
    plt.close()
    print("  03_price_by_brand.png")


def chart_purpose_distribution():
    fig, ax = plt.subplots(figsize=(10, 5))
    sorted_purposes = sorted(purpose_labels.items(), key=lambda x: -x[1])
    names = [p[0] for p in sorted_purposes]
    counts = [p[1] for p in sorted_purposes]
    bars = ax.barh(names[::-1], counts[::-1], color=COLORS[:len(names)])
    ax.set_xlabel("Number of Laptops")
    ax.set_title("Laptops by Purpose Label", fontsize=14, fontweight="bold", pad=15)
    for bar, val in zip(bars, counts[::-1]):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "04_purpose_distribution.png"))
    plt.close()
    print("  04_purpose_distribution.png")


def chart_ram_vs_price():
    fig, ax = plt.subplots(figsize=(10, 5))
    r_data = [(r["RAM_GB"], r["Price_NPR"]) for r in rows if r["RAM_GB"] > 0 and r["Price_NPR"] > 0]
    x = [d[0] for d in r_data]
    y = [d[1] for d in r_data]
    ax.scatter(x, y, alpha=0.15, s=8, color=HIGHLIGHT)
    ax.set_xlabel("RAM (GB)")
    ax.set_ylabel("Price (NPR)")
    ax.set_title("RAM vs Price", fontsize=14, fontweight="bold", pad=15)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_npr))
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(x), max(x), 100)
    ax.plot(x_line, p(x_line), color="#e9c46a", linestyle="--", linewidth=2, label="Trend")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "05_ram_vs_price.png"))
    plt.close()
    print("  05_ram_vs_price.png")


def chart_cpu_gpu_tier():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    cpu_counts = [0] * 7
    for t in cpu_tiers:
        cpu_counts[t] += 1
    axes[0].bar(range(1, 7), cpu_counts[1:], color=COLORS[:6])
    axes[0].set_xlabel("CPU Tier")
    axes[0].set_ylabel("Count")
    axes[0].set_title("CPU Tier Distribution", fontsize=12, fontweight="bold")
    axes[0].set_xticks(range(1, 7))

    gpu_counts = [0] * 7
    for t in gpu_tiers:
        gpu_counts[t] += 1
    axes[1].bar(range(1, 7), gpu_counts[1:], color=COLORS[:6])
    axes[1].set_xlabel("GPU Tier")
    axes[1].set_ylabel("Count")
    axes[1].set_title("GPU Tier Distribution", fontsize=12, fontweight="bold")
    axes[1].set_xticks(range(1, 7))

    plt.suptitle("CPU & GPU Tier Distributions (1=Budget, 6=High-end)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "06_cpu_gpu_tiers.png"), bbox_inches="tight")
    plt.close()
    print("  06_cpu_gpu_tiers.png")


def chart_correlation_heatmap():
    import matplotlib.colors as mcolors
    features = ["RAM_GB", "Storage_GB", "Screen_Size_Inches", "Weight_KG", "Price_NPR"]
    feature_labels = ["RAM", "Storage", "Screen", "Weight", "Price"]
    data = []
    for r in rows:
        row_vals = [r[f] for f in features]
        data.append(row_vals)
    data = [d for d in data if all(v > 0 for v in d)]

    arr = np.array(data)
    n = len(features)
    corr = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            corr[i, j] = np.corrcoef(arr[:, i], arr[:, j])[0, 1]

    fig, ax = plt.subplots(figsize=(8, 6))
    cmap = mcolors.LinearSegmentedColormap.from_list("custom", ["#0f3460", "#1a1a2e", "#e94560"])
    im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(feature_labels, rotation=45, ha="right")
    ax.set_yticklabels(feature_labels)
    for i in range(n):
        for j in range(n):
            color = "white" if abs(corr[i, j]) > 0.5 else "#e0e0e0"
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", color=color, fontsize=11)
    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "07_correlation_heatmap.png"))
    plt.close()
    print("  07_correlation_heatmap.png")


def chart_storage_vs_price():
    fig, ax = plt.subplots(figsize=(10, 5))
    storage_colors = {"SSD": "#e94560", "HDD": "#0f3460", "Flash Storage": "#533483"}
    for stype, color in storage_colors.items():
        x = [r["Storage_GB"] for r in rows if r["Storage_GB"] > 0 and r["Storage_Type"] == stype and r["Price_NPR"] > 0]
        y = [r["Price_NPR"] for r in rows if r["Storage_GB"] > 0 and r["Storage_Type"] == stype and r["Price_NPR"] > 0]
        if x:
            ax.scatter(x, y, alpha=0.2, s=8, color=color, label=stype)
    ax.set_xlabel("Storage (GB)")
    ax.set_ylabel("Price (NPR)")
    ax.set_title("Storage vs Price by Type", fontsize=14, fontweight="bold", pad=15)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_npr))
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "08_storage_vs_price.png"))
    plt.close()
    print("  08_storage_vs_price.png")


if __name__ == "__main__":
    print("Generating charts...")
    chart_price_distribution()
    chart_brand_market_share()
    chart_price_by_brand()
    chart_purpose_distribution()
    chart_ram_vs_price()
    chart_cpu_gpu_tier()
    chart_correlation_heatmap()
    chart_storage_vs_price()
    print(f"\nAll charts saved to {OUT_DIR}/")
