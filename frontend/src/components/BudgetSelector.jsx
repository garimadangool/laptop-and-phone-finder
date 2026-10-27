import { BUDGET_MAX, BUDGET_MIN, BUDGET_PRESETS, BUDGET_STEP, formatNpr } from "../data/options";
import "./BudgetSelector.css";

export default function BudgetSelector({ value, onChange, min, max, step, presets }) {
  const bMin = min ?? BUDGET_MIN;
  const bMax = max ?? BUDGET_MAX;
  const bStep = step ?? BUDGET_STEP;
  const bPresets = presets ?? BUDGET_PRESETS;
  const fill = ((value - bMin) / (bMax - bMin)) * 100;
  const activePreset = bPresets.find((p) => p.value === value);

  function fmtScaleLabel(n) {
    if (n >= 100000) return `Rs. ${n / 100000}L`;
    if (n >= 1000) return `Rs. ${n / 1000}K`;
    return `Rs. ${n}`;
  }

  const scaleLabels = [bMin, Math.round((bMin + bMax) / 2), bMax].map(fmtScaleLabel);

  return (
    <div className="budget">
      <div className="budget__top">
        <span className="budget__label">💰 Your budget</span>
        <div className="budget__value">
          {formatNpr(value)}
          <small>maximum spend</small>
        </div>
      </div>

      <div className="budget__presets" role="group" aria-label="Quick budget picks">
        {bPresets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            className={`budget-preset ${activePreset === preset ? "is-active" : ""}`}
            aria-pressed={activePreset === preset}
            onClick={() => onChange(preset.value)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="budget__slider-wrap">
        <input
          className="budget__slider"
          style={{ "--fill": `${fill}%` }}
          type="range"
          min={bMin}
          max={bMax}
          step={bStep}
          value={value}
          aria-label="Maximum budget in Nepali rupees"
          onChange={(e) => onChange(Number(e.target.value))}
        />
        <div className="budget__scale" aria-hidden="true">
          {scaleLabels.map((lbl) => (
            <span key={lbl}>{lbl}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
