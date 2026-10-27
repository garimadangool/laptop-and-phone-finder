import { useEffect, useState } from "react";
import "./Navbar.css";

const LAPTOP_LINKS = [
  { label: "Home", href: "#home" },
  { label: "Find Laptop", href: "#finder" },
  { label: "Insights", href: "#insights" },
  { label: "Compare", href: "#results" },
  { label: "About", href: "#about" },
];

const PHONE_LINKS = [
  { label: "Home", href: "#home" },
  { label: "Find Phone", href: "#finder" },
  { label: "Insights", href: "#insights" },
  { label: "Compare", href: "#results" },
  { label: "About", href: "#about" },
];

export default function Navbar({ productType = "laptop", onSwitch }) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = productType === "phone" ? PHONE_LINKS : LAPTOP_LINKS;
  const isLaptop = productType === "laptop";

  return (
    <header className={`navbar ${scrolled ? "navbar--scrolled" : ""}`}>
      <div className="container navbar__inner">
        <a className="navbar__logo" href="#home" onClick={() => setOpen(false)}>
          <span className="navbar__logo-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
              <path
                d="M13 2 4.5 13.5h5L9 22l8.5-11.5h-5L13 2Z"
                fill="#fff"
              />
            </svg>
          </span>
          <span className="navbar__wordmark">
            Laptop<em>Finder</em>
            <small>.np</small>
          </span>
        </a>

        <nav
          className={`navbar__links ${open ? "is-open" : ""}`}
          aria-label="Main navigation"
        >
          {links.map((link) => (
            <a key={link.label} href={link.href} onClick={() => setOpen(false)}>
              {link.label}
            </a>
          ))}

          {onSwitch && (
            <button
              type="button"
              className={`navbar__switch-btn ${!isLaptop ? "navbar__switch-btn--active" : ""}`}
              onClick={() => {
                onSwitch(isLaptop ? "phone" : "laptop");
                setOpen(false);
              }}
              aria-label={isLaptop ? "Switch to phone finder" : "Switch to laptop finder"}
            >
              {isLaptop ? "📱 Find Phone" : "💻 Find Laptop"}
            </button>
          )}

          <a className="navbar__cta" href="#finder" onClick={() => setOpen(false)}>
            Start Shopping
          </a>
        </nav>

        <button
          type="button"
          className="navbar__toggle"
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  );
}
