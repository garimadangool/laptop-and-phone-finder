import { useId, useState } from "react";
import "./SpecTip.css";

// Small hover/tap tooltip that explains a spec in plain, non-technical words.
export default function SpecTip({ children }) {
  const [open, setOpen] = useState(false);
  const id = useId();

  return (
    <span
      className="spec-tip"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="spec-tip__btn"
        aria-label="What does this mean?"
        aria-describedby={open ? id : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">
          <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M9.5 9.5a2.5 2.5 0 1 1 3.4 2.3c-.9.3-1.4 1-1.4 1.9v.3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <circle cx="12" cy="17.5" r="1.1" fill="currentColor" />
        </svg>
      </button>
      {open && (
        <span className="spec-tip__bubble" id={id} role="tooltip">
          {children}
        </span>
      )}
    </span>
  );
}