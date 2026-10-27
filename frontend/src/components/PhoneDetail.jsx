import { useEffect } from "react";
import { formatNpr } from "../data/options";
import "./LaptopDetail.css";

function scoreClass(score) {
  if (score >= 85) return "high";
  if (score >= 70) return "mid";
  return "low";
}

export default function PhoneDetail({ rec, onClose, onToggleCompare, isFavorited, onToggleFavorite }) {
  const { laptop: phone, score } = rec;
  const reasons = rec.reasons || [];
  const penalties = rec.penalties || [];

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const chipFamily = phone.chipset_family || "Other";
  const chipTier = phone.chipset_tier || "—";

  const specs = [
    ["Chipset", `${phone.chipset || "—"} (Tier ${chipTier})`],
    ["Chipset family", chipFamily],
    ["GPU", phone.gpu || "—"],
    ["Memory", `${phone.ram_gb} GB RAM`],
    [
      "Storage",
      phone.storage_gb > 0
        ? `${phone.storage_gb >= 1024 ? `${phone.storage_gb / 1024} TB` : `${phone.storage_gb} GB`} ${phone.storage_type}`
        : "—",
    ],
    [
      "Display",
      phone.display_size > 0
        ? `${phone.display_size}" ${phone.display_type || ""}`
        : "—",
    ],
    ["Battery", phone.battery_mah > 0 ? `${phone.battery_mah} mAh` : "—"],
    ["Fast charging", phone.fast_charging_w > 0 ? `${phone.fast_charging_w}W` : "—"],
    ["Rear camera", phone.rear_camera_mp > 0 ? `${phone.rear_camera_mp} MP` : "—"],
    ["Front camera", phone.front_camera_mp > 0 ? `${phone.front_camera_mp} MP` : "—"],
    ["OIS", phone.has_ois === "Yes" ? "Yes" : "No"],
    ["5G", phone.has_5g === "Yes" ? "Yes" : "No"],
    ["NFC", phone.has_nfc === "Yes" ? "Yes" : "No"],
    ["Fingerprint", phone.has_fingerprint === "Yes" ? "Yes" : "No"],
    ["Weight", phone.weight_grams > 0 ? `${phone.weight_grams} g` : "—"],
    ["Operating system", phone.os || "—"],
    ["Suited for", phone.purpose],
  ].filter(([, value]) => value && value !== "—" || (typeof value === "string" && value !== "—"));

  return (
    <div className="detail-backdrop" onClick={onClose}>
      <div
        className="detail-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`${phone.brand} phone details`}
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="detail-close" aria-label="Close details" onClick={onClose}>
          ✕
        </button>

        <header className="detail-head">
          <div>
            <span className="detail-brand">{phone.brand}</span>
            <h3>{phone.product_name}</h3>
            <p className="detail-gpu">{phone.chipset || ""}</p>
          </div>
          <div className={`score-pill score-pill--${scoreClass(score)}`}>
            <strong>{Math.round(score)}%</strong>
            <small>match</small>
          </div>
        </header>

        <div className="detail-price-row">
          <span className="detail-price">{formatNpr(phone.price_npr)}</span>
          <span className="detail-price-note">price in NPR</span>
        </div>

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

        <section className="detail-section">
          <h4>✅ Why it was recommended</h4>
          <ul className="detail-reasons">
            {reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </section>

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

        <footer className="detail-actions">
          <button
            type="button"
            className={`btn-askai${isFavorited ? " btn-askai--saved" : ""}`}
            title={isFavorited ? "Remove from saved phones" : "Save this phone"}
            aria-pressed={isFavorited}
            onClick={() => onToggleFavorite(rec)}
          >
            {isFavorited ? "💔 Saved" : "🤍 Save"}
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
