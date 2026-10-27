import { useState } from "react";
import { formatNpr } from "../data/options";
import { logClick } from "../services/api";
import { favoriteId } from "../services/favorites";
import LaptopVisual from "./LaptopVisual";
import PhoneVisual from "./PhoneVisual";
import "./ResultsSection.css";

const INITIAL_VISIBLE = 6;

const SORT_OPTIONS = [
  { id: "rank", label: "Best match" },
  { id: "price-asc", label: "Price: low → high" },
  { id: "price-desc", label: "Price: high → low" },
  { id: "ram", label: "Most RAM" },
  { id: "storage", label: "Most storage" },
];

const PHONE_SORT_OPTIONS = [
  { id: "rank", label: "Best match" },
  { id: "price-asc", label: "Price: low → high" },
  { id: "price-desc", label: "Price: high → low" },
  { id: "ram", label: "Most RAM" },
  { id: "battery", label: "Best battery" },
];

function scoreClass(score) {
  if (score >= 85) return "high";
  if (score >= 70) return "mid";
  return "low";
}

function cleanTitle(laptop) {
  const model = (laptop.cpu_model || "").replace(/^processor/i, "").trim();
  const name = `${laptop.brand} ${model}`.trim();
  return name.length > 46 ? `${name.slice(0, 44)}…` : name || laptop.brand;
}

function SpecPill({ icon, label }) {
  return (
    <span className="spec-pill">
      <span aria-hidden="true">{icon}</span> {label}
    </span>
  );
}

function DealBadge({ deal }) {
  if (!deal || !deal.tier) return null;
  const isDeal = deal.tier === "great" || deal.tier === "good";
  if (!isDeal && deal.tier !== "premium") return null;
  return (
    <span
      className={`deal-badge deal-badge--${deal.tier}`}
      title={deal.note || (isDeal ? "Good value" : "Premium pricing")}
    >
      <span aria-hidden="true">{isDeal ? "🏷️" : "💸"}</span>
      {deal.tier === "great" ? "Great deal" : deal.tier === "good" ? "Good value" : deal.tier === "premium" ? "Premium" : null}
    </span>
  );
}

export function LaptopCard({ rec, rank, onViewDetails, onToggleCompare, isSelected, compareFull, isFavorited = false, onToggleFavorite, productType = "laptop" }) {
  const { laptop, score, reasons, penalties, deal } = rec;
  const isBest = rank === 0;
  const isPhone = productType === "phone";

  return (
    <article className={`laptop-card ${isBest ? "is-best" : ""}`}>
      <div className="laptop-card__flavor">
        {isBest && (
          <span className="best-badge">
            <span aria-hidden="true">🏆</span> Best Match
          </span>
        )}
        {onToggleFavorite && (
          <button
            type="button"
            className={`fav-btn ${isFavorited ? "is-fav" : ""}`}
            aria-pressed={isFavorited}
            aria-label={isFavorited ? `Remove from saved ${isPhone ? "phones" : "laptops"}` : `Save this ${isPhone ? "phone" : "laptop"}`}
            title={isFavorited ? "Remove from saved list" : "Save to your list"}
            onClick={() => onToggleFavorite(rec)}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill={isFavorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1 7.8 7.8 7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8Z" />
            </svg>
          </button>
        )}
      </div>

      <div className="laptop-card__top">
        {isPhone ? (
          <PhoneVisual brand={laptop.brand} />
        ) : (
          <LaptopVisual brand={laptop.brand} />
        )}

        <div className="laptop-card__heading">
          <h4>{isPhone ? (laptop.product_name || `${laptop.brand} ${laptop.chipset || ""}`) : cleanTitle(laptop)}</h4>
          <p className="laptop-card__gpu">
            {isPhone
              ? (laptop.chipset || "Unknown chipset")
              : ((laptop.gpu_brand && laptop.gpu_model ? `${laptop.gpu_brand} ${laptop.gpu_model}` : laptop.gpu_model) || "Integrated graphics")
            }
          </p>
        </div>

        <div className={`score-pill score-pill--${scoreClass(score)}`}>
          <strong>{Math.round(score)}%</strong>
          <small>match</small>
        </div>
      </div>

      <div className="laptop-card__badges">
        <DealBadge deal={deal} />
        {!isPhone && laptop.weight_kg > 0 && laptop.weight_kg <= 1.6 && (
          <span className="weight-badge" title="Portable (≤1.6 kg)">
            <span aria-hidden="true">🍃</span> Light
          </span>
        )}
        {isPhone && laptop.has_5g === "Yes" && (
          <span className="weight-badge" title="5G enabled">
            <span aria-hidden="true">📶</span> 5G
          </span>
        )}
      </div>

      <div className="laptop-card__specs">
        {isPhone ? (
          <>
            <SpecPill icon="🧠" label={laptop.chipset || "Unknown chipset"} />
            <SpecPill icon="⚡" label={`${laptop.ram_gb} GB RAM`} />
            {laptop.storage_gb > 0 && (
              <SpecPill icon="💾" label={`${laptop.storage_gb} GB ${laptop.storage_type}`} />
            )}
            {laptop.battery_mah > 0 && <SpecPill icon="🔋" label={`${laptop.battery_mah} mAh`} />}
            {laptop.rear_camera_mp > 0 && <SpecPill icon="📸" label={`${laptop.rear_camera_mp} MP`} />}
            {laptop.display_size > 0 && <SpecPill icon="📱" label={`${laptop.display_size}" ${laptop.display_type || ""}`} />}
          </>
        ) : (
          <>
            <SpecPill icon="🧠" label={`${laptop.cpu_brand} ${laptop.cpu_model}`.trim()} />
            <SpecPill icon="⚡" label={`${laptop.ram_gb} GB RAM`} />
            {laptop.storage_gb > 0 && (
              <SpecPill
                icon="💾"
                label={`${laptop.storage_gb >= 1024 ? `${laptop.storage_gb / 1024} TB` : `${laptop.storage_gb} GB`} ${laptop.storage_type}`}
              />
            )}
            {laptop.screen_size > 0 && (
              <SpecPill icon="🖥️" label={`${laptop.screen_size}"${laptop.touchscreen ? " • Touch" : ""}`} />
            )}
            {laptop.weight_kg > 0 && <SpecPill icon="⚖️" label={`${laptop.weight_kg} kg`} />}
            {laptop.os && laptop.os !== "Unknown" && <SpecPill icon="💿" label={laptop.os} />}
          </>
        )}
      </div>

      <ul className="reasons">
        {reasons.slice(0, 3).map((r) => (
          <li key={r}>
            <span className="tick" aria-hidden="true">✓</span> {r}
          </li>
        ))}
      </ul>

      {penalties.length > 0 && (
        <ul className="penalties">
          {penalties.slice(0, 2).map((p) => (
            <li key={p}>
              <span aria-hidden="true">⚠</span> {p}
            </li>
          ))}
        </ul>
      )}

      <div className="laptop-card__footer">
        <span className="price">{formatNpr(laptop.price_npr)}</span>
        <div className="laptop-card__actions">
          <button
            type="button"
            className="btn-details"
            onClick={() => onViewDetails(rec)}
          >
            View Details
          </button>
          <button
            type="button"
            className={`btn-compare ${isSelected ? "is-active" : ""}`}
            disabled={!isSelected && compareFull}
            title={
              isSelected
                ? "Remove from comparison"
                : compareFull
                  ? `You can compare up to 4 ${isPhone ? "phones" : "laptops"}`
                  : "Add to side-by-side comparison"
            }
            onClick={() => onToggleCompare(rec)}
          >
            {isSelected ? "✓ Added" : "⇄ Compare"}
          </button>
        </div>
      </div>
    </article>
  );
}

function SkeletonCard() {
  return (
    <div className="laptop-card sk-card" aria-hidden="true">
      <div className="laptop-card__top">
        <div className="sk sk-visual" />
        <div className="sk-stack">
          <div className="sk sk-title" />
          <div className="sk sk-sub" />
        </div>
        <div className="sk sk-score" />
      </div>
      <div className="laptop-card__specs">
        <span className="sk sk-pill" />
        <span className="sk sk-pill" />
        <span className="sk sk-pill" />
      </div>
      <div className="sk sk-line" />
      <div className="sk sk-line short" />
      <div className="laptop-card__footer">
        <div className="sk sk-price" />
        <div className="sk sk-btn" />
      </div>
    </div>
  );
}

function sortRecs(recs, sortId) {
  const list = recs.slice();
  switch (sortId) {
    case "price-asc":
      return list.sort((a, b) => a.laptop.price_npr - b.laptop.price_npr);
    case "price-desc":
      return list.sort((a, b) => b.laptop.price_npr - a.laptop.price_npr);
    case "ram":
      return list.sort((a, b) => b.laptop.ram_gb - a.laptop.ram_gb);
    case "storage":
      return list.sort((a, b) => b.laptop.storage_gb - a.laptop.storage_gb);
    case "battery":
      return list.sort((a, b) => (b.laptop.battery_mah || 0) - (a.laptop.battery_mah || 0));
    default:
      return list.sort((a, b) => b.score - a.score);
  }
}

export default function ResultsSection({ results, loading = false, onViewDetails, compare = [], onToggleCompare, favorites = [], onToggleFavorite, productType = "laptop" }) {
  const [state, setState] = useState({
    lastResults: results,
    visibleCount: INITIAL_VISIBLE,
    sortId: "rank",
    dealsOnly: false,
  });

  if (results !== state.lastResults) {
    setState((s) => ({ ...s, lastResults: results, visibleCount: INITIAL_VISIBLE, sortId: "rank", dealsOnly: false }));
  }

  const filtered = state.dealsOnly
    ? results.filter((r) => r.deal?.tier === "great" || r.deal?.tier === "good")
    : results;

  const sorted = sortRecs(filtered, state.sortId);
  const visibleResults = sorted.slice(0, state.visibleCount);
  const hiddenCount = sorted.length - visibleResults.length;
  const dealsCount = results.filter((r) => r.deal?.tier === "great" || r.deal?.tier === "good").length;

  const isPhone = productType === "phone";
  const sortOpts = isPhone ? PHONE_SORT_OPTIONS : SORT_OPTIONS;
  const noun = isPhone ? "phones" : "laptops";

  return (
    <section className="section results" id="results">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">{loading ? "⏳ Searching the catalogue…" : "✨ Your Matches"}</span>
          <h2>{loading ? "Finding your best matches…" : `Hand-picked ${noun} recommendations.`}</h2>
          <p>Ranked by our scoring engine — budget fit, purpose fit and raw specs all weighed in.</p>
        </div>

        {loading ? (
          <div className="results__grid" role="status" aria-label="Loading recommendations">
            {Array.from({ length: INITIAL_VISIBLE }, (_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : results.length === 0 ? (
          <div className="results__empty">
            <span className="results__empty-icon" aria-hidden="true">🛍️</span>
            <h3>Your picks will show up here</h3>
            <p>
              Choose a purpose and budget above, then hit{" "}
              <strong>{`Find My ${isPhone ? "Phone" : "Laptop"}`}</strong> to see your best matches.
            </p>
          </div>
        ) : (
          <>
            <div className="results__toolbar" role="toolbar" aria-label="Sort and filter results">
              <div className="results__sort" role="group" aria-label="Sort recommendations">
                {sortOpts.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    className={`chip-btn ${state.sortId === opt.id ? "is-active" : ""}`}
                    aria-pressed={state.sortId === opt.id}
                    onClick={() => {
                      logClick("sort", null, { sort: opt.id });
                      setState((s) => ({ ...s, sortId: opt.id, visibleCount: INITIAL_VISIBLE }));
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              {dealsCount > 0 && (
                <button
                  type="button"
                  className={`results__deals ${state.dealsOnly ? "is-active" : ""}`}
                  aria-pressed={state.dealsOnly}
                  title={`Show only items we score as great/good value (${dealsCount} available)`}
                  onClick={() => {
                    logClick("filter_deals", null, { on: !state.dealsOnly });
                    setState((s) => ({ ...s, dealsOnly: !s.dealsOnly, visibleCount: INITIAL_VISIBLE }));
                  }}
                >
                  🏷️ Deals only
                  <small>{dealsCount}</small>
                </button>
              )}
              <p className="results__count" aria-live="polite">
                {filtered.length === results.length
                  ? `${results.length} ${noun} found`
                  : `Showing ${filtered.length} of ${results.length} ${noun}`}
              </p>
            </div>

            <div className="results__grid">
              {visibleResults.map((rec, i) => (
                <LaptopCard
                  key={`${rec.laptop.brand}-${i}`}
                  rec={rec}
                  rank={i}
                  onViewDetails={onViewDetails}
                  isSelected={compare.includes(rec)}
                  compareFull={compare.length >= 4 && !compare.includes(rec)}
                  onToggleCompare={onToggleCompare}
                  isFavorited={favorites.some((f) => f.id === favoriteId(rec))}
                  onToggleFavorite={onToggleFavorite}
                  productType={productType}
                />
              ))}
            </div>
            {hiddenCount > 0 && (
              <div className="results__more">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    logClick("show_more", null, { position: state.visibleCount });
                    setState((s) => ({ ...s, visibleCount: s.visibleCount + INITIAL_VISIBLE }));
                  }}
                >
                  Show more {noun} ({hiddenCount} more) ↓
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
