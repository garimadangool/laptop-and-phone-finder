export const PHONE_PURPOSES = [
  { label: "Gaming", emoji: "🎮", blurb: "Fast chipsets, high refresh rates" },
  { label: "Camera", emoji: "📸", blurb: "High MP, OIS, pro video" },
  { label: "Student", emoji: "📚", blurb: "Budget-friendly, all-day battery" },
  { label: "General Use", emoji: "🌐", blurb: "Browsing, social media, calls" },
  { label: "Heavy Multitasking", emoji: "🗂️", blurb: "8GB+ RAM, smooth switching" },
  { label: "Fast Performance", emoji: "⚡", blurb: "Flagship chipsets, blazing fast" },
  { label: "Battery Life", emoji: "🔋", blurb: "5000mAh+, all-day power" },
];

export const PHONE_BUDGET_MIN = 5000;
export const PHONE_BUDGET_MAX = 200000;
export const PHONE_BUDGET_STEP = 1000;

export const PHONE_BUDGET_PRESETS = [
  { label: "Under 10K", value: 10000 },
  { label: "10K – 20K", value: 20000 },
  { label: "20K – 40K", value: 40000 },
  { label: "40K – 80K", value: 80000 },
  { label: "80K+", value: 150000 },
];

export const PHONE_RAM_OPTIONS = [
  { label: "Any", value: null },
  { label: "4 GB", value: 4 },
  { label: "6 GB", value: 6 },
  { label: "8 GB", value: 8 },
  { label: "12 GB", value: 12 },
];

export const PHONE_STORAGE_OPTIONS = [
  { label: "Any", value: null },
  { label: "64 GB", value: 64 },
  { label: "128 GB", value: 128 },
  { label: "256 GB", value: 256 },
  { label: "512 GB", value: 512 },
];

export const PHONE_CHIPSET_TIERS = [
  { tier: 1, label: "Entry", hint: "Helio A22, SD 439…" },
  { tier: 2, label: "Basic", hint: "Helio G25, SD 460…" },
  { tier: 3, label: "Mid-range", hint: "Helio G99, SD 695…" },
  { tier: 4, label: "Upper Mid", hint: "Dimensity 7300, SD 7…" },
  { tier: 5, label: "Flagship-tier", hint: "Dimensity 9300, SD 8 Gen 2…" },
  { tier: 6, label: "Top Flagship", hint: "SD 8 Elite, A18 Pro…" },
];

export const PHONE_FALLBACK_BRANDS = [
  "Samsung", "Xiaomi", "Vivo", "Realme", "OPPO",
  "OnePlus", "Apple", "Motorola", "Honor", "iQOO",
  "Tecno", "Infinix", "Nokia", "Nothing", "Google",
];
