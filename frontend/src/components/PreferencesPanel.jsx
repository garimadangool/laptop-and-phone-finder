import {
  CPU_TIERS,
  FALLBACK_BRANDS,
  GPU_TIERS,
  RAM_OPTIONS,
  SCREEN_OPTIONS,
  STORAGE_OPTIONS,
  STORAGE_TYPE_OPTIONS,
} from "../data/options";
import SpecTip from "./SpecTip";
import "./PreferencesPanel.css";

function ChipGroup({ legend, options, value, onSelect, hint, tip }) {
  return (
    <fieldset className="prefs__group">
      <legend className="prefs__legend">
        {legend}
        {tip && <SpecTip>{tip}</SpecTip>}
      </legend>
      <div className="chip-row" role="group" aria-label={legend}>
        {options.map((opt) => {
          const isActive = value === opt.value;
          return (
            <button
              key={opt.label}
              type="button"
              className={`chip-btn ${hint ? "tier-chip" : ""} ${isActive ? "is-active" : ""}`}
              aria-pressed={isActive}
              onClick={() => onSelect(opt.value)}
            >
              {opt.label}
              {hint && opt.hint && <small>{opt.hint}</small>}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

function ToggleCard({ title, hint, checked, onChange, tip }) {
  return (
    <label className={`toggle-card ${checked ? "is-on" : ""}`}>
      <span className="toggle-card__text">
        <span className="toggle-card__title">
          {title}
          {tip && <SpecTip>{tip}</SpecTip>}
        </span>
        <span className="toggle-card__hint">{hint}</span>
      </span>
      <span className="switch">
        <input type="checkbox" checked={checked} onChange={onChange} />
        <span className="switch__track" />
        <span className="switch__thumb" />
      </span>
    </label>
  );
}

export default function PreferencesPanel({ form, setField }) {
  const chipProps = (name) => ({
    value: form[name],
    onSelect: (v) => setField(name, v),
  });

  const tierOptions = (tiers) =>
    [{ label: "Any", value: null }, ...tiers.map((t) => ({ ...t, value: t.tier }))];

  return (
    <div className="prefs">
      <ChipGroup
        legend="Memory (RAM)"
        tip="How many apps you can keep open at once. 8 GB is plenty for office & browsing; 16 GB+ if you do heavy multitasking."
        options={RAM_OPTIONS}
        {...chipProps("minRam")}
      />

      <ChipGroup
        legend="Storage space"
        tip="How many files, apps and videos you can save. 512 GB is a comfy middle ground for most people."
        options={STORAGE_OPTIONS}
        {...chipProps("minStorage")}
      />

      <ChipGroup
        legend="Storage type"
        tip="SSD is much faster — boots and opens apps in seconds. HDD is slower and better for bulk, cheap storage."
        options={STORAGE_TYPE_OPTIONS.map((t) => ({ label: t, value: t === "Any" ? null : t }))}
        {...chipProps("storageType")}
      />

      <fieldset className="prefs__group">
        <legend className="prefs__legend">
          Brand preference
          <SpecTip>Love a specific brand, or just want the best deal? Give a brand a head-start — or leave at "Any brand".</SpecTip>
        </legend>
        <select
          className="brand-select"
          value={form.brand}
          onChange={(e) => setField("brand", e.target.value)}
          aria-label="Brand preference"
        >
          <option value="">Any brand</option>
          {(form.brandOptions || FALLBACK_BRANDS).map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
      </fieldset>

      <ChipGroup
        legend="Processor power"
        hint
        tip="The 'brain' of the laptop. i5 / Ryzen 5 is enough for everyday work; i7+ only for heavy coding, editing or 3D."
        options={tierOptions(CPU_TIERS)}
        {...chipProps("minCpuTier")}
      />

      <ChipGroup
        legend="Graphics power"
        hint
        tip="The GPU draws the images. For office, browsing and videos, a basic one is plenty — a strong GPU is only for gaming or video editing."
        options={tierOptions(GPU_TIERS)}
        {...chipProps("minGpuTier")}
      />

      <ChipGroup
        legend="Screen size (min)"
        tip={"Bigger screen = more room to work, but a heavier laptop. 14–15 inches is the sweet spot for most."}
        options={SCREEN_OPTIONS}
        {...chipProps("minScreen")}
      />

      <div className="toggle-row">
        <ToggleCard
          title="Touchscreen"
          hint="Tap, draw and scribble on screen"
          tip="Lets you poke and swipe the screen like a tablet. Nice-to-have, not essential."
          checked={form.touchscreen}
          onChange={(e) => setField("touchscreen", e.target.checked)}
        />
        <ToggleCard
          title="Dedicated GPU"
          hint="NVIDIA / AMD graphics required"
          tip="A separate graphics card. Only worth it for gaming, video editing or 3D work — office laptops don't need one."
          checked={form.dedicatedGpu}
          onChange={(e) => setField("dedicatedGpu", e.target.checked)}
        />
      </div>
    </div>
  );
}
