import {
  PHONE_CHIPSET_TIERS,
  PHONE_FALLBACK_BRANDS,
  PHONE_RAM_OPTIONS,
  PHONE_STORAGE_OPTIONS,
} from "../data/phoneOptions";
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

export default function PhonePreferencesPanel({ form, setField }) {
  const chipProps = (name) => ({
    value: form[name],
    onSelect: (v) => setField(name, v),
  });

  const tierOptions = [{ label: "Any", value: null }, ...PHONE_CHIPSET_TIERS.map((t) => ({ ...t, value: t.tier }))];

  return (
    <div className="prefs">
      <ChipGroup
        legend="Memory (RAM)"
        tip="How many apps can stay open at once. 4–6 GB is fine for basic use; 8 GB+ feels smoother for multitasking and gaming."
        options={PHONE_RAM_OPTIONS}
        {...chipProps("minRam")}
      />

      <ChipGroup
        legend="Storage space"
        tip="How many photos, apps and videos you can keep. 128 GB is a comfortable starting point for most people."
        options={PHONE_STORAGE_OPTIONS}
        {...chipProps("minStorage")}
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
          {(form.brandOptions || PHONE_FALLBACK_BRANDS).map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </fieldset>

      <ChipGroup
        legend="Chipset power"
        hint
        tip="The 'brain' of the phone. Mid-range handles calls, social and apps fine; a flagship chip only matters for heavy gaming."
        options={tierOptions}
        {...chipProps("minChipsetTier")}
      />

      <div className="toggle-row">
        <ToggleCard
          title="5G Required"
          hint="5G connectivity needed"
          tip="Faster mobile internet where 5G is available. Nice for the future — not a must for everyone."
          checked={form.require5g}
          onChange={(e) => setField("require5g", e.target.checked)}
        />
        <ToggleCard
          title="NFC Required"
          hint="Contactless payments & pairing"
          tip="The chip that lets you tap-to-pay and pair quickly with other devices."
          checked={form.requireNfc}
          onChange={(e) => setField("requireNfc", e.target.checked)}
        />
        <ToggleCard
          title="Fingerprint Required"
          hint="Biometric unlock sensor"
          tip="Unlock your phone with your fingerprint — fast and secure. Most newer phones have one."
          checked={form.requireFingerprint}
          onChange={(e) => setField("requireFingerprint", e.target.checked)}
        />
      </div>
    </div>
  );
}
