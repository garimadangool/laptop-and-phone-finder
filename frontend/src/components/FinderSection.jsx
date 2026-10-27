import { useEffect, useRef, useState } from "react";
import {
  getBrands, getRecommendations, beginSearch, logSearch,
  getPhoneBrands, getPhoneRecommendations,
} from "../services/api";
import PurposeGrid from "./PurposeGrid";
import BudgetSelector from "./BudgetSelector";
import PreferencesPanel from "./PreferencesPanel";
import PhonePreferencesPanel from "./PhonePreferencesPanel";
import {
  PHONE_PURPOSES, PHONE_BUDGET_PRESETS,
  PHONE_BUDGET_MIN, PHONE_BUDGET_MAX, PHONE_BUDGET_STEP,
} from "../data/phoneOptions";
import "./FinderSection.css";

const STEP_PURPOSE = 0;
const STEP_BUDGET = 1;
const STEP_PREFS = 2;

const LAPTOP_INITIAL = {
  purpose: [],
  budget: 100000,
  minRam: null,
  minStorage: null,
  storageType: null,
  brand: "",
  brandOptions: [],
  minCpuTier: null,
  minGpuTier: null,
  minScreen: null,
  touchscreen: false,
  dedicatedGpu: false,
};

const PHONE_INITIAL = {
  purpose: [],
  budget: 30000,
  minRam: null,
  minStorage: null,
  brand: "",
  brandOptions: [],
  minChipsetTier: null,
  minCameraMp: null,
  minBattery: null,
  require5g: false,
  requireNfc: false,
  requireFingerprint: false,
};

function getInitialForm(productType) {
  return productType === "phone" ? { ...PHONE_INITIAL } : { ...LAPTOP_INITIAL };
}

function intOrNull(v) {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : null;
}

function formFromUrl(seed, productType) {
  const params = new URLSearchParams(window.location.search);
  const form = { ...seed };

  const purposes = params.get("purpose");
  if (purposes) form.purpose = purposes.split("+").filter(Boolean);

  const budget = intOrNull(params.get("budget"));
  if (budget != null) {
    if (productType === "phone" && budget >= PHONE_BUDGET_MIN) form.budget = budget;
    else if (productType === "laptop" && budget >= 25000) form.budget = budget;
  }

  if (productType === "laptop") {
    const hasPrefs = ["ram", "storage", "storage_type", "brand", "cpu", "gpu", "screen", "touch", "gpu_dedicated"]
      .some((k) => params.get(k) != null);
    if (hasPrefs) {
      form.minRam = intOrNull(params.get("ram"));
      form.minStorage = intOrNull(params.get("storage"));
      form.storageType = params.get("storage_type") || null;
      form.brand = params.get("brand") || "";
      form.minCpuTier = intOrNull(params.get("cpu"));
      form.minGpuTier = intOrNull(params.get("gpu"));
      form.minScreen = intOrNull(params.get("screen"));
      form.touchscreen = params.get("touch") === "1";
      form.dedicatedGpu = params.get("gpu_dedicated") === "1";
    }
  } else {
    const hasPrefs = ["ram", "storage", "brand", "chipset", "5g", "nfc", "fingerprint"]
      .some((k) => params.get(k) != null);
    if (hasPrefs) {
      form.minRam = intOrNull(params.get("ram"));
      form.minStorage = intOrNull(params.get("storage"));
      form.brand = params.get("brand") || "";
      form.minChipsetTier = intOrNull(params.get("chipset"));
      form.require5g = params.get("5g") === "1";
      form.requireNfc = params.get("nfc") === "1";
      form.requireFingerprint = params.get("fingerprint") === "1";
    }
  }

  return form;
}

function syncUrl(form, productType) {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams();

  if (form.purpose.length > 0) {
    params.set("purpose", form.purpose.join("+"));
    params.set("budget", String(form.budget));
  }
  if (form.minRam != null) params.set("ram", String(form.minRam));
  if (form.minStorage != null) params.set("storage", String(form.minStorage));
  if (form.brand) params.set("brand", form.brand);

  if (productType === "laptop") {
    if (form.storageType) params.set("storage_type", form.storageType);
    if (form.minCpuTier != null) params.set("cpu", String(form.minCpuTier));
    if (form.minGpuTier != null) params.set("gpu", String(form.minGpuTier));
    if (form.minScreen != null) params.set("screen", String(form.minScreen));
    if (form.touchscreen) params.set("touch", "1");
    if (form.dedicatedGpu) params.set("gpu_dedicated", "1");
  } else {
    if (form.minChipsetTier != null) params.set("chipset", String(form.minChipsetTier));
    if (form.require5g) params.set("5g", "1");
    if (form.requireNfc) params.set("nfc", "1");
    if (form.requireFingerprint) params.set("fingerprint", "1");
  }

  const qs = params.toString();
  const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState(null, "", next);
}

export default function FinderSection({ onResults, onLoadingChange, productType = "laptop" }) {
  const [form, setForm] = useState(() =>
    typeof window !== "undefined" && window.location.search
      ? formFromUrl(getInitialForm(productType), productType)
      : getInitialForm(productType)
  );
  const [step, setStep] = useState(STEP_PURPOSE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const setField = (name, value) =>
    setForm((prev) => ({ ...prev, [name]: value }));

  const togglePurpose = (label) =>
    setForm((prev) => ({
      ...prev,
      purpose: prev.purpose.includes(label)
        ? prev.purpose.filter((p) => p !== label)
        : [...prev.purpose, label],
    }));

  const isPhone = productType === "phone";
  const budgetMin = isPhone ? PHONE_BUDGET_MIN : 25000;
  const budgetMax = isPhone ? PHONE_BUDGET_MAX : 300000;
  const budgetStep = isPhone ? PHONE_BUDGET_STEP : 1000;

  // Load brands from backend
  useEffect(() => {
    let cancelled = false;
    const fetcher = isPhone ? getPhoneBrands : getBrands;
    fetcher()
      .then((data) => {
        if (!cancelled && Array.isArray(data.brands)) {
          const sorted = [...data.brands].sort((a, b) =>
            a.toLowerCase().localeCompare(b.toLowerCase())
          );
          setField("brandOptions", sorted);
        }
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [isPhone]);

  // Reset form when switching product type
  useEffect(() => {
    setForm(getInitialForm(productType));
    setStep(STEP_PURPOSE);
    setError("");
  }, [productType]);

  // Auto-run from shared/bookmarked URL
  const autoSearched = useRef(false);
  useEffect(() => {
    if (autoSearched.current || form.purpose.length === 0) return;
    if (typeof window === "undefined") return;
    const fromShared = window.location.search.includes("purpose=");
    if (!fromShared) return;
    autoSearched.current = true;
    handleFind();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleFind() {
    if (form.purpose.length === 0) {
      setError("Please pick at least one use — it shapes the whole recommendation. You can choose several!");
      setStep(STEP_PURPOSE);
      return;
    }
    setError("");
    setLoading(true);
    onLoadingChange?.(true);
    try {
      const payload = isPhone
        ? {
            budget: String(form.budget),
            purpose: form.purpose.join(" and "),
            min_ram: form.minRam,
            min_storage: form.minStorage,
            brand: form.brand || null,
            min_chipset_tier: form.minChipsetTier,
            min_camera_mp: form.minCameraMp,
            min_battery: form.minBattery,
            require_5g: form.require5g,
            require_nfc: form.requireNfc,
            require_fingerprint: form.requireFingerprint,
            top_n: 12,
          }
        : {
            budget: String(form.budget),
            purpose: form.purpose.join(" and "),
            min_ram: form.minRam,
            min_storage: form.minStorage,
            storage_type: form.storageType,
            brand: form.brand || null,
            min_cpu_tier: form.minCpuTier,
            min_gpu_tier: form.minGpuTier,
            min_screen: form.minScreen,
            touchscreen: form.touchscreen,
            dedicated_gpu: form.dedicatedGpu,
            top_n: 12,
          };

      const sid = beginSearch();
      const fetcher = isPhone ? getPhoneRecommendations : getRecommendations;
      const data = await fetcher(payload);
      const recs = (data.recommendations || []).map((rec, i) => ({
        ...rec,
        _rank: i + 1,
        _sid: sid,
      }));
      logSearch(payload, data);
      onResults(recs);
      syncUrl(form, productType);
      requestAnimationFrame(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      onLoadingChange?.(false);
    }
  }

  function scrollStepIntoView(i) {
    requestAnimationFrame(() => {
      document.getElementById(`finder-step-${i}`)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  function goNext() {
    setError("");
    const next = Math.min(step + 1, STEP_PREFS);
    setStep(next);
    scrollStepIntoView(next);
  }

  function goBack() {
    setError("");
    const prev = Math.max(step - 1, STEP_PURPOSE);
    setStep(prev);
    scrollStepIntoView(prev);
  }

  function jumpTo(i) {
    setError("");
    setStep(i);
    scrollStepIntoView(i);
  }

  function reset() {
    setForm(getInitialForm(productType));
    setStep(STEP_PURPOSE);
    setError("");
    if (typeof window !== "undefined" && window.location.search) {
      history.replaceState(null, "", window.location.pathname);
    }
  }

  const budgetPresets = isPhone ? PHONE_BUDGET_PRESETS : undefined;

  const stepTitles = [
    ["What will you use it for?", "Pick one — or mix several, like Gaming + Photography."],
    ["What's your budget?", "Be honest — we'll find the best value at your price."],
    ["Any must-haves?", "Totally optional — skip ahead if you don't mind."],
  ];

  function finderStep(index) {
    const showPurpose = index === STEP_PURPOSE;
    const showBudget = index === STEP_BUDGET;
    const showPrefs = index === STEP_PREFS;
    return (
      <div key={index} id={`finder-step-${index}`} className="finder__step">
        <span className="finder__step-num" aria-hidden="true">{index + 1}</span>
        <h3>{stepTitles[index][0]}</h3>
        <p className="finder__optional">{stepTitles[index][1]}</p>

        {showPurpose && (
          isPhone ? (
            <div className="purpose-grid" role="group" aria-label="What will you use the phone for?">
              {PHONE_PURPOSES.map((purpose) => {
                const isSelected = form.purpose.includes(purpose.label);
                return (
                  <button
                    key={purpose.label}
                    type="button"
                    className={`purpose-card ${isSelected ? "is-selected" : ""}`}
                    aria-pressed={isSelected}
                    onClick={() => togglePurpose(purpose.label)}
                  >
                    <span className="purpose-card__check" aria-hidden="true">✓</span>
                    <span className="purpose-card__emoji" aria-hidden="true">{purpose.emoji}</span>
                    <span className="purpose-card__name">{purpose.label}</span>
                    <span className="purpose-card__blurb">{purpose.blurb}</span>
                  </button>
                );
              })}
            </div>
          ) : (
            <PurposeGrid selected={form.purpose} onToggle={togglePurpose} />
          )
        )}

        {showBudget && (
          <BudgetSelector
            value={form.budget}
            onChange={(v) => setField("budget", v)}
            min={budgetMin}
            max={budgetMax}
            step={budgetStep}
            presets={budgetPresets}
          />
        )}

        {showPrefs && (
          isPhone ? (
            <PhonePreferencesPanel form={form} setField={setField} />
          ) : (
            <PreferencesPanel form={form} setField={setField} />
          )
        )}

        {showPrefs && (
          <div className="finder__actions">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={reset}
              disabled={loading}
            >
              ↺ Reset
            </button>
            <button type="button" className="btn btn-primary" onClick={handleFind} disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" aria-hidden="true" /> Hunting…
                </>
              ) : (
                <>Find My {isPhone ? "Phone" : "Laptop"} →</>
              )}
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <section className="section finder" id="finder">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">🧭 {isPhone ? "Phone" : "Laptop"} Finder</span>
          <h2>Tell us what you need — we'll do the hunting.</h2>
          <p>Three quick steps. No spec-sheet degree required.</p>
        </div>

        <div className="finder__steps">
          {[STEP_PURPOSE, STEP_BUDGET, STEP_PREFS].map(finderStep)}
        </div>

        {error && (
          <p className="finder__error" role="alert" style={{ marginTop: "1.2rem" }}>
            ⚠ {error}
          </p>
        )}

        <p className="finder__share-hint">
          🔗 After searching, your filters are saved to the link — copy it to
          share or bookmark this exact search.
        </p>
      </div>
    </section>
  );
}