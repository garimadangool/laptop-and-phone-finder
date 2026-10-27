// All option data used by the finder UI.
// Purpose labels MUST match ALL_PURPOSE_LABELS in model/recommend.py.

export const PURPOSES = [
  { label: "Gaming", emoji: "🎮", blurb: "High FPS, dedicated GPUs, fast screens" },
  { label: "Programming", emoji: "💻", blurb: "Fast CPU, comfy RAM for code & builds" },
  { label: "Video Editing", emoji: "🎬", blurb: "Strong GPU + big, quick storage" },
  { label: "Graphic Design", emoji: "🎨", blurb: "Color-accurate, smooth visuals" },
  { label: "Student", emoji: "📚", blurb: "Light, portable and budget friendly" },
  { label: "Office", emoji: "💼", blurb: "Reliable all-rounders for work" },
  { label: "AI / Machine Learning", emoji: "🤖", blurb: "Serious GPU + RAM horsepower" },
  { label: "General Use", emoji: "🌐", blurb: "Browsing, streaming, everyday tasks" },
  { label: "Fast Performance", emoji: "⚡", blurb: "Snappy machines that just fly" },
  { label: "Heavy Multitasking", emoji: "🗂️", blurb: "Tons of tabs? Bring the RAM" },
];

export const BUDGET_MIN = 25000;
export const BUDGET_MAX = 300000;
export const BUDGET_STEP = 5000;

export const BUDGET_PRESETS = [
  { label: "Under 50K", value: 50000 },
  { label: "50K – 80K", value: 80000 },
  { label: "80K – 1 Lakh", value: 100000 },
  { label: "1 – 1.5 Lakh", value: 150000 },
  { label: "1.5 Lakh+", value: 200000 },
];

export const RAM_OPTIONS = [
  { label: "Any RAM", value: null },
  { label: "8 GB", value: 8 },
  { label: "16 GB", value: 16 },
  { label: "32 GB", value: 32 },
];

export const STORAGE_OPTIONS = [
  { label: "Any", value: null },
  { label: "256 GB", value: 256 },
  { label: "512 GB", value: 512 },
  { label: "1 TB", value: 1024 },
];

export const STORAGE_TYPE_OPTIONS = ["Any", "SSD", "HDD"];

export const SCREEN_OPTIONS = [
  { label: "Any size", value: null },
  { label: '13"', value: 13 },
  { label: '14"', value: 14 },
  { label: '15"', value: 15 },
  { label: '17"', value: 17 },
];

// Tier scales mirror model/recommend.py CPU_TIERS / GPU_TIERS.
export const CPU_TIERS = [
  { tier: 1, label: "Entry", hint: "Celeron, Pentium…" },
  { tier: 2, label: "Basic", hint: "i3, Ryzen 3…" },
  { tier: 3, label: "Mainstream", hint: "i5, Ryzen 5…" },
  { tier: 4, label: "Performance", hint: "i7, Ryzen 7…" },
  { tier: 5, label: "Enthusiast", hint: "i9, Ryzen 9…" },
  { tier: 6, label: "Workstation", hint: "HX, M-series…" },
];

export const GPU_TIERS = [
  { tier: 1, label: "Entry", hint: "Basic integrated" },
  { tier: 2, label: "Light", hint: "UHD, Iris, MX…" },
  { tier: 3, label: "Casual", hint: "GTX 1650, RTX 3050…" },
  { tier: 4, label: "Gaming", hint: "RTX 4050, 4060…" },
  { tier: 5, label: "High-end", hint: "RTX 4070–4090…" },
  { tier: 6, label: "Extreme", hint: "Flagship mobile GPUs" },
];

// Fallback list; the live list is fetched from GET /brands at runtime.
export const FALLBACK_BRANDS = [
  "Acer",
  "Apple",
  "ASUS",
  "Dell",
  "HP",
  "Lenovo",
  "LG",
  "MSI",
  "Microsoft",
  "Samsung",
  "Infinix",
  "Xiaomi",
];

export function formatNpr(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 0,
  }).format(value);
}
