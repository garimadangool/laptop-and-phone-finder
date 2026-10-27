import { useEffect, useRef } from "react";
import { formatNpr } from "../data/options";
import "./CompareModal.css";

const LAPTOP_ROWS = [
  { label: "Price", render: (rec) => formatNpr(rec.laptop.price_npr), value: (rec) => rec.laptop.price_npr, better: "low" },
  { label: "Match score", render: (rec) => `${Math.round(rec.score)}%`, value: (rec) => rec.score, better: "high" },
  { label: "Processor", render: (rec) => [rec.laptop.cpu_brand, rec.laptop.cpu_model].filter(Boolean).join(" ") || "—", value: (rec) => rec.laptop.cpu_tier, better: "high" },
  { label: "CPU tier", render: (rec) => `${rec.laptop.cpu_tier} / 6`, value: (rec) => rec.laptop.cpu_tier, better: null },
  { label: "Graphics", render: (rec) => [rec.laptop.gpu_brand, rec.laptop.gpu_model].filter(Boolean).join(" ") || "Integrated", value: (rec) => rec.laptop.gpu_tier, better: null },
  { label: "GPU tier", render: (rec) => `${rec.laptop.gpu_tier} / 6`, value: (rec) => rec.laptop.gpu_tier, better: "high" },
  { label: "Memory", render: (rec) => `${rec.laptop.ram_gb} GB`, value: (rec) => rec.laptop.ram_gb, better: "high" },
  { label: "Storage", render: (rec) => rec.laptop.storage_gb > 0 ? `${rec.laptop.storage_gb >= 1024 ? `${rec.laptop.storage_gb / 1024} TB` : `${rec.laptop.storage_gb} GB`} ${rec.laptop.storage_type}` : "—", value: (rec) => rec.laptop.storage_gb, better: "high" },
  { label: "Display", render: (rec) => rec.laptop.screen_size > 0 ? `${rec.laptop.screen_size}"${rec.laptop.touchscreen ? " • Touch" : ""}` : "—", value: () => null, better: null },
  { label: "Weight", render: (rec) => rec.laptop.weight_kg > 0 ? `${rec.laptop.weight_kg} kg` : "—", value: (rec) => rec.laptop.weight_kg > 0 ? rec.laptop.weight_kg : null, better: "low" },
  { label: "Operating system", render: (rec) => rec.laptop.os !== "Unknown" ? rec.laptop.os : "—", value: () => null, better: null },
  { label: "Suited for", render: (rec) => rec.laptop.purpose, value: () => null, better: null },
];

const PHONE_ROWS = [
  { label: "Price", render: (rec) => formatNpr(rec.laptop.price_npr), value: (rec) => rec.laptop.price_npr, better: "low" },
  { label: "Match score", render: (rec) => `${Math.round(rec.score)}%`, value: (rec) => rec.score, better: "high" },
  { label: "Chipset", render: (rec) => rec.laptop.chipset || "—", value: (rec) => rec.laptop.chipset_tier, better: "high" },
  { label: "Chipset tier", render: (rec) => `${rec.laptop.chipset_tier} / 6`, value: (rec) => rec.laptop.chipset_tier, better: "high" },
  { label: "GPU", render: (rec) => rec.laptop.gpu || "—", value: () => null, better: null },
  { label: "Memory", render: (rec) => `${rec.laptop.ram_gb} GB`, value: (rec) => rec.laptop.ram_gb, better: "high" },
  { label: "Storage", render: (rec) => rec.laptop.storage_gb > 0 ? `${rec.laptop.storage_gb} GB ${rec.laptop.storage_type}` : "—", value: (rec) => rec.laptop.storage_gb, better: "high" },
  { label: "Display", render: (rec) => rec.laptop.display_size > 0 ? `${rec.laptop.display_size}" ${rec.laptop.display_type || ""}` : "—", value: (rec) => rec.laptop.display_size, better: null },
  { label: "Battery", render: (rec) => rec.laptop.battery_mah > 0 ? `${rec.laptop.battery_mah} mAh` : "—", value: (rec) => rec.laptop.battery_mah, better: "high" },
  { label: "Fast charging", render: (rec) => rec.laptop.fast_charging_w > 0 ? `${rec.laptop.fast_charging_w}W` : "—", value: (rec) => rec.laptop.fast_charging_w, better: "high" },
  { label: "Rear camera", render: (rec) => rec.laptop.rear_camera_mp > 0 ? `${rec.laptop.rear_camera_mp} MP` : "—", value: (rec) => rec.laptop.rear_camera_mp, better: "high" },
  { label: "Front camera", render: (rec) => rec.laptop.front_camera_mp > 0 ? `${rec.laptop.front_camera_mp} MP` : "—", value: (rec) => rec.laptop.front_camera_mp, better: null },
  { label: "5G", render: (rec) => rec.laptop.has_5g === "Yes" ? "Yes" : "No", value: (rec) => rec.laptop.has_5g === "Yes" ? 1 : 0, better: "high" },
  { label: "NFC", render: (rec) => rec.laptop.has_nfc === "Yes" ? "Yes" : "No", value: (rec) => rec.laptop.has_nfc === "Yes" ? 1 : 0, better: "high" },
  { label: "Fingerprint", render: (rec) => rec.laptop.has_fingerprint === "Yes" ? "Yes" : "No", value: (rec) => rec.laptop.has_fingerprint === "Yes" ? 1 : 0, better: "high" },
  { label: "Weight", render: (rec) => rec.laptop.weight_grams > 0 ? `${rec.laptop.weight_grams} g` : "—", value: (rec) => rec.laptop.weight_grams > 0 ? rec.laptop.weight_grams : null, better: "low" },
  { label: "OS", render: (rec) => rec.laptop.os || "—", value: () => null, better: null },
  { label: "Suited for", render: (rec) => rec.laptop.purpose, value: () => null, better: null },
];

function bestIndexes(items, row) {
  if (!row.better) return new Set();
  const values = items.map(row.value);
  const valid = values.filter((v) => v !== null && v !== undefined);
  if (valid.length < 2) return new Set();
  const target = row.better === "low" ? Math.min(...valid) : Math.max(...valid);
  const winners = values.map((v, i) => (v === target ? i : -1)).filter((i) => i >= 0);
  return winners.length === valid.length ? new Set() : new Set(winners);
}

export default function CompareModal({ items, onClose, productType = "laptop" }) {
  const scrollRef = useRef(null);
  const drag = useRef(null);
  const isPhone = productType === "phone";
  const ROWS = isPhone ? PHONE_ROWS : LAPTOP_ROWS;

  function onPointerDown(e) {
    if (e.pointerType === "touch") return;
    const el = scrollRef.current;
    if (!el || el.scrollWidth <= el.clientWidth) return;
    drag.current = { x: e.clientX, left: el.scrollLeft };
    el.classList.add("is-dragging");
  }

  function onPointerMove(e) {
    if (!drag.current || !scrollRef.current) return;
    scrollRef.current.scrollLeft = drag.current.left - (e.clientX - drag.current.x);
  }

  function endDrag() {
    drag.current = null;
    if (scrollRef.current) scrollRef.current.classList.remove("is-dragging");
  }

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div className="compare-backdrop" onClick={onClose}>
      <div
        className="compare-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`${isPhone ? "Phone" : "Laptop"} comparison`}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="compare-head">
          <div>
            <span className="eyebrow">⇄ Side-by-side</span>
            <h3>Comparing {items.length} {isPhone ? "phones" : "laptops"}</h3>
          </div>
          <button type="button" className="compare-close" aria-label="Close comparison" onClick={onClose}>
            ✕
          </button>
        </header>

        <div
          ref={scrollRef}
          className="compare-scroll"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={endDrag}
          onPointerLeave={endDrag}
        >
          <table className="compare-table">
            <thead>
              <tr>
                <th scope="col" className="compare-table__label-col">Spec</th>
                {items.map((rec) => (
                  <th key={rec.laptop.brand + (rec.laptop.product_name || rec.laptop.cpu_model || "")} scope="col">
                    <span className="compare-col__brand">{rec.laptop.brand}</span>
                    <span className="compare-col__cpu">
                      {isPhone
                        ? (rec.laptop.chipset || rec.laptop.product_name || "")
                        : [rec.laptop.cpu_brand, rec.laptop.cpu_model].filter(Boolean).join(" ")
                      }
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => {
                const best = bestIndexes(items, row);
                return (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    {items.map((rec, col) => (
                      <td key={col} className={best.has(col) ? "is-best" : ""}>
                        {row.render(rec)}
                        {best.has(col) && <span className="best-tag" title="Best in this row">★</span>}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="compare-swipe-hint" aria-hidden="true">
          ← swipe the table sideways to see all {isPhone ? "phones" : "laptops"} →
        </p>

        <p className="compare-note">
          ★ marks the best value in each row (lowest price/weight, highest score/specs).
          Ties are not marked.
        </p>
      </div>
    </div>
  );
}
