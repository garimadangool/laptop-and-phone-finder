// Per-brand laptop illustrations for result cards.
// Themes cover every brand present in data/laptops_ml_ready.csv;
// unknown brands fall back to a hashed colour tint.

const THEMES = {
  hp:        { ink: "#0096d6", bg: "#e6f4fb", mark: "hp", ring: true },
  lenovo:    { ink: "#e2231a", bg: "#fdeaea", mark: "lenovo" },
  asus:      { ink: "#0a3d7a", bg: "#e8eff9", mark: "ASUS", accent: "#00b3e3", style: "gaming" },
  dell:      { ink: "#007db8", bg: "#e6f4fb", mark: "DELL" },
  msi:       { ink: "#e30613", bg: "#fdeaea", mark: "MSI", style: "gaming", italic: true },
  acer:      { ink: "#83b81a", bg: "#f2f8e5", mark: "acer" },
  apple:     { ink: "#6e6e73", bg: "#efeff1", mark: "MacBook", style: "ultra" },
  samsung:   { ink: "#1428a0", bg: "#eaedf9", mark: "SAMSUNG" },
  microsoft: { ink: "#737373", bg: "#efefef", mark: "Microsoft" },
  infinix:   { ink: "#21a366", bg: "#e6f5ee", mark: "Infinix" },
  xiaomi:    { ink: "#ff6900", bg: "#fff1e6", mark: "Xiaomi" },
  lg:        { ink: "#a50034", bg: "#fae8ec", mark: "LG" },
  razer:     { ink: "#161616", bg: "#ecf9e7", mark: "RAZER", accent: "#44d62c", style: "gaming" },
  alienware: { ink: "#18181b", bg: "#e6f7fb", mark: "ALIENWARE", accent: "#18c8ff", style: "gaming" },
  gigabyte:  { ink: "#ff6a00", bg: "#fff1e6", mark: "GIGABYTE", style: "gaming" },
  aorus:     { ink: "#1f1f1f", bg: "#fff1e6", mark: "AORUS", accent: "#ff6a00", style: "gaming" },
  huawei:    { ink: "#cf0a2c", bg: "#fbe9eb", mark: "HUAWEI" },
  honor:     { ink: "#0092bc", bg: "#e5f6fb", mark: "HONOR" },
  toshiba:   { ink: "#d40e14", bg: "#fdeaea", mark: "TOSHIBA" },
  dynabook:  { ink: "#007d8a", bg: "#e4f5f7", mark: "dynabook" },
  fujitsu:   { ink: "#e60012", bg: "#fdeaea", mark: "FUJITSU" },
  google:    { ink: "#4285f4", bg: "#e8f0fe", mark: "Google" },
  chuwi:     { ink: "#5c6bc0", bg: "#eceef9", mark: "CHUWI" },
  mediacom:  { ink: "#005bab", bg: "#e5eff8", mark: "MEDIACOM" },
  vero:      { ink: "#78b938", bg: "#f1f8e4", mark: "VERO" },
};

const TINTS = ["#2337b8", "#7c3aed", "#0f766e", "#b45309", "#be185d"];

function fallbackTheme(brand) {
  let hash = 0;
  for (const ch of brand.toLowerCase()) hash = (hash * 31 + ch.charCodeAt(0)) % 997;
  return {
    id: `x${hash}`,
    ink: TINTS[hash % TINTS.length],
    bg: "#eef0f7",
    mark: brand.slice(0, 4).toUpperCase(),
  };
}

function resolveTheme(brand = "") {
  const key = brand.trim().toLowerCase();
  if (THEMES[key]) return { id: key, ...THEMES[key] };
  return fallbackTheme(brand.trim() || "?");
}

function shade(hex, factor) {
  const n = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16));
  return `rgb(${Math.round(r * factor)} ${Math.round(g * factor)} ${Math.round(b * factor)})`;
}

function markFontSize(mark) {
  if (mark.length <= 3) return 5.2;
  if (mark.length <= 6) return 4.1;
  return 3.3;
}

function Mark({ mark, ring, italic }) {
  if (!mark) return null;
  if (ring) {
    return (
      <>
        <circle cx="48" cy="39" r="4.4" fill="none" stroke="#fff" strokeWidth="1.1" opacity="0.95" />
        <text x="48" y="40.6" textAnchor="middle" fontSize="4.4" fontWeight="800" fontStyle="italic" fill="#fff">hp</text>
      </>
    );
  }
  return (
    <text
      x="48"
      y="40.5"
      textAnchor="middle"
      fontSize={markFontSize(mark)}
      fontWeight="800"
      fontStyle={italic ? "italic" : undefined}
      letterSpacing={mark.length > 6 ? 0.5 : 0.9}
      fill="#fff"
      opacity="0.95"
    >
      {mark}
    </text>
  );
}

export default function LaptopVisual({ brand = "" }) {
  const t = resolveTheme(brand);
  const base = shade(t.ink, 0.82);
  const accent = t.accent || t.ink;

  return (
    <div className="laptop-visual" style={{ background: t.bg }} aria-hidden="true">
      <svg viewBox="0 0 96 64" focusable="false">
        <defs>
          <linearGradient id={`scr-${t.id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ffffff" />
            <stop offset="1" stopColor="#e9edf6" />
          </linearGradient>
        </defs>

        <ellipse cx="48" cy="58.5" rx="32" ry="2.4" fill="#0f172a" opacity="0.06" />

        {/* Lid + screen */}
        {t.style === "ultra" ? (
          <>
            <rect x="14" y="5" width="68" height="37" rx="4" fill={t.ink} />
            <rect x="17.5" y="8" width="61" height="27" rx="2" fill={`url(#scr-${t.id})`} />
          </>
        ) : t.style === "gaming" ? (
          <>
            <polygon points="21,5 75,5 80,10 80,38 76,43 20,43 16,38 16,10" fill={t.ink} />
            <rect x="19.5" y="8.5" width="57" height="24.5" rx="1" fill={`url(#scr-${t.id})`} />
            <rect x="19.5" y="33.2" width="57" height="0.9" fill={accent} opacity="0.9" />
          </>
        ) : (
          <>
            <rect x="16" y="5" width="64" height="38" rx="3" fill={t.ink} />
            <rect x="19" y="8" width="58" height="26" rx="1.5" fill={`url(#scr-${t.id})`} />
          </>
        )}

        {!t.style && !t.ring && (
          <circle cx="48" cy="6.5" r="0.9" fill="#fff" opacity="0.8" />
        )}

        <Mark mark={t.mark} ring={t.ring} italic={t.italic} />

        {/* Base deck */}
        {t.style === "ultra" ? (
          <path d="M12 44 H84 L86.5 49 Q87 50.5 85 50.5 H11 Q9 50.5 9.5 49 Z" fill={base} />
        ) : (
          <path d="M11 45 H85 L88.5 51 Q89 53 87 53 H9 Q7 53 7.5 51 Z" fill={base} />
        )}
        <rect x="42" y="46.2" width="12" height="2" rx="1" fill="#fff" opacity="0.4" />

        {t.style === "gaming" && (
          <g fill={accent} opacity="0.85">
            <rect x="15" y="47.4" width="6" height="1.2" rx="0.6" />
            <rect x="23" y="47.4" width="6" height="1.2" rx="0.6" />
            <rect x="67" y="47.4" width="6" height="1.2" rx="0.6" />
            <rect x="75" y="47.4" width="6" height="1.2" rx="0.6" />
          </g>
        )}
      </svg>
      <span className="laptop-visual__brand">{brand}</span>
    </div>
  );
}
