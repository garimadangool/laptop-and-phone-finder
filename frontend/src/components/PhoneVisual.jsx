const THEMES = {
  samsung:   { ink: "#1428a0", bg: "#eaedf9", mark: "SAMSUNG" },
  apple:     { ink: "#6e6e73", bg: "#efeff1", mark: "Apple" },
  xiaomi:    { ink: "#ff6900", bg: "#fff1e6", mark: "Xiaomi" },
  vivo:      { ink: "#415fff", bg: "#eceef9", mark: "vivo" },
  realme:    { ink: "#ffc300", bg: "#fff9e6", mark: "realme", markColor: "#1a1a1a" },
  oppo:      { ink: "#1a8c37", bg: "#e6f5ec", mark: "OPPO" },
  oneplus:   { ink: "#e30613", bg: "#fdeaea", mark: "OnePlus" },
  motorola:  { ink: "#5c2d91", bg: "#ede6f7", mark: "Moto" },
  honor:     { ink: "#0092bc", bg: "#e5f6fb", mark: "HONOR" },
  iqoo:      { ink: "#1a1a2e", bg: "#e8e8f0", mark: "iQOO" },
  tecno:     { ink: "#0066cc", bg: "#e6f0ff", mark: "TECNO" },
  infinix:   { ink: "#21a366", bg: "#e6f5ee", mark: "Infinix" },
  nokia:     { ink: "#124191", bg: "#e6ecf9", mark: "NOKIA" },
  nothing:   { ink: "#1a1a1a", bg: "#f0f0f0", mark: "Nothing" },
  google:    { ink: "#4285f4", bg: "#e8f0fe", mark: "Google" },
  huawei:    { ink: "#cf0a2c", bg: "#fbe9eb", mark: "HUAWEI" },
  lenovo:    { ink: "#e2231a", bg: "#fdeaea", mark: "Lenovo" },
  asus:      { ink: "#0a3d7a", bg: "#e8eff9", mark: "ASUS" },
  hp:        { ink: "#0096d6", bg: "#e6f4fb", mark: "hp", ring: true },
  dell:      { ink: "#007db8", bg: "#e6f4fb", mark: "DELL" },
  acer:      { ink: "#83b81a", bg: "#f2f8e5", mark: "acer" },
  sony:      { ink: "#000000", bg: "#efefef", mark: "SONY" },
};

const TINTS = ["#2337b8", "#7c3aed", "#0f766e", "#b45309", "#be185d"];

function fallbackTheme(brand) {
  let hash = 0;
  for (const ch of brand.toLowerCase()) hash = (hash * 31 + ch.charCodeAt(0)) % 997;
  return {
    id: `x${hash}`,
    ink: TINTS[hash % TINTS.length],
    bg: "#eef0f7",
    mark: brand.slice(0, 6).toUpperCase(),
  };
}

function resolveTheme(brand = "") {
  const key = brand.trim().toLowerCase();
  if (THEMES[key]) return { id: key, ...THEMES[key] };
  return fallbackTheme(brand.trim() || "?");
}

function markFontSize(mark) {
  if (mark.length <= 4) return 5.5;
  if (mark.length <= 6) return 4.2;
  return 3.2;
}

function Mark({ mark, markColor }) {
  if (!mark) return null;
  return (
    <text
      x="24"
      y="30"
      textAnchor="middle"
      fontSize={markFontSize(mark)}
      fontWeight="800"
      letterSpacing={mark.length > 5 ? 0.4 : 0.7}
      fill={markColor || "#fff"}
      opacity="0.95"
    >
      {mark}
    </text>
  );
}

export default function PhoneVisual({ brand = "" }) {
  const t = resolveTheme(brand);

  return (
    <div className="phone-visual" style={{ background: t.bg }} aria-hidden="true">
      <svg viewBox="0 0 48 80" focusable="false">
        {/* Phone body */}
        <rect x="6" y="2" width="36" height="76" rx="8" fill={t.ink} />

        {/* Screen */}
        <rect x="9" y="10" width="30" height="58" rx="3" fill="#e9edf6" />

        {/* Notch */}
        <rect x="18" y="4" width="12" height="4" rx="2" fill="#fff" opacity="0.15" />

        {/* Camera dot */}
        <circle cx="24" cy="6" r="1.2" fill="#fff" opacity="0.5" />

        <Mark mark={t.mark} markColor={t.markColor} />

        {/* Home indicator */}
        <rect x="18" y="71" width="12" height="2" rx="1" fill="#fff" opacity="0.3" />
      </svg>
      <span className="phone-visual__brand">{brand}</span>
    </div>
  );
}
