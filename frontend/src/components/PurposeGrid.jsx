import { PURPOSES } from "../data/options";
import "./PurposeGrid.css";

export default function PurposeGrid({ selected, onToggle }) {
  return (
    <div className="purpose-grid" role="group" aria-label="What will you use the laptop for?">
      {PURPOSES.map((purpose) => {
        const isSelected = selected.includes(purpose.label);
        return (
          <button
            key={purpose.label}
            type="button"
            className={`purpose-card ${isSelected ? "is-selected" : ""}`}
            aria-pressed={isSelected}
            onClick={() => onToggle(purpose.label)}
          >
            <span className="purpose-card__check" aria-hidden="true">✓</span>
            <span className="purpose-card__emoji" aria-hidden="true">
              {purpose.emoji}
            </span>
            <span className="purpose-card__name">{purpose.label}</span>
            <span className="purpose-card__blurb">{purpose.blurb}</span>
          </button>
        );
      })}
    </div>
  );
}
