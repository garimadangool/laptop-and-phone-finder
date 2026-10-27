import { useEffect, useState } from "react";
import { formatNpr } from "../data/options";
import AskAiPanel from "./AskAiPanel";
import "./LaptopDetail.css";

function scoreClass(score) {
  if (score >= 85) return "high";
  if (score >= 70) return "mid";
  return "low";
}

export default function LaptopDetail({ rec, onClose, onToggleCompare, isFavorited, onToggleFavorite, onViewLaptop }) {
  const { laptop, score } = rec;
  // Saved items from FavoritesSection may not carry reasons/penalties.
  const reasons = rec.reasons || [];
  const penalties = rec.penalties || [];
  const [askOpen, setAskOpen] = useState(false);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const gpuName =
    [laptop.gpu_brand, laptop.gpu_model].filter(Boolean).join(" ") ||
    "Integrated graphics";

  const specs = [
    ["Processor", `${laptop.cpu_brand} ${laptop.cpu_model}`.trim()],
    ["CPU tier", `${laptop.cpu_tier} / 6`],
    ["Graphics", gpuName],
    ["GPU tier", `${laptop.gpu_tier} / 6`],
    ["Memory", `${laptop.ram_gb} GB RAM`],
    [
      "Storage",
      laptop.storage_gb > 0
        ? `${laptop.storage_gb >= 1024 ? `${laptop.storage_gb / 1024} TB` : `${laptop.storage_gb} GB`} ${laptop.storage_type}`
        : null,
    ],
    [
      "Display",
      laptop.screen_size > 0
        ? `${laptop.screen_size}"${laptop.touchscreen ? " • Touchscreen" : ""}`
        : null,
    ],
    ["Operating system", laptop.os !== "Unknown" ? laptop.os : null],
    ["Weight", laptop.weight_kg > 0 ? `${laptop.weight_kg} kg` : null],
    ["Suited for", laptop.purpose],
  ].filter(([, value]) => value);

  return (
    <div className="detail-backdrop" onClick={onClose}>
      <div
        className="detail-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`${laptop.brand} laptop details`}
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="detail-close" aria-label="Close details" onClick={onClose}>
          ✕
        </button>

        {/* Header */}
        <header className="detail-head">
          <div>
            <span className="detail-brand">{laptop.brand}</span>
            <h3>{`${laptop.cpu_brand} ${laptop.cpu_model}`.trim()}</h3>
            <p className="detail-gpu">{gpuName}</p>
          </div>
          <div className={`score-pill score-pill--${scoreClass(score)}`}>
            <strong>{Math.round(score)}%</strong>
            <small>match</small>
          </div>
        </header>

        <div className="detail-price-row">
          <span className="detail-price">{formatNpr(laptop.price_npr)}</span>
          <span className="detail-price-note">price in NPR</span>
        </div>

        {/* Full specifications */}
        <section className="detail-section">
          <h4>Full specifications</h4>
          <dl className="detail-specs">
            {specs.map(([label, value]) => (
              <div key={label} className="detail-spec-row">
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* Why recommended */}
        <section className="detail-section">
          <h4>✅ Why it was recommended</h4>
          <ul className="detail-reasons">
            {reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </section>

        {/* Weaknesses */}
        <section className="detail-section">
          <h4>⚠️ Things to consider</h4>
          {penalties.length > 0 ? (
            <ul className="detail-penalties">
              {penalties.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          ) : (
            <p className="detail-no-penalty">No notable weaknesses found for your requirements.</p>
          )}
        </section>

        {/* Ask AI chat */}
        {askOpen && (
          <AskAiPanel
            key={`${laptop.brand}-${laptop.cpu_model}-${laptop.price_npr}`}
            rec={rec}
            onViewLaptop={onViewLaptop}
          />
        )}

        {/* Actions */}
        <footer className="detail-actions">
          <button
            type="button"
            className={`btn-askai${isFavorited ? " btn-askai--saved" : ""}`}
            title={isFavorited ? "Remove from saved laptops" : "Save this laptop"}
            aria-pressed={isFavorited}
            onClick={() => onToggleFavorite(rec)}
          >
            {isFavorited ? "💔 Saved" : "🤍 Save"}
          </button>
          <button
            type="button"
            className={`btn-askai${askOpen ? " btn-askai--active" : ""}`}
            aria-expanded={askOpen}
            title="Ask the AI assistant about this laptop"
            onClick={() => setAskOpen((open) => !open)}
          >
            🤖 Ask AI
            <small>{askOpen ? "close" : "beta"}</small>
          </button>
          <button
            type="button"
            className="btn-compare-lg"
            title="Add to side-by-side comparison"
            onClick={() => {
              onToggleCompare(rec);
              onClose();
            }}
          >
            ⇄ Compare
          </button>
        </footer>
      </div>
    </div>
  );
}
