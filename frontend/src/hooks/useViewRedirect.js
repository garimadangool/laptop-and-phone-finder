import { useEffect, useRef } from "react";

// Sends the user back to the top of the page (home) whenever the viewport
// crosses the mobile breakpoint — e.g. when they shrink the window from
// laptop width down to phone width. Clears any deep-link hash / query so they
// land on a fresh home page instead of a scrolled-to section.
export function useViewRedirect() {
  const wasMobile = useRef(
    typeof window !== "undefined"
      ? (window.innerWidth < 768)
      : false
  );

  useEffect(() => {
    function onResize() {
      const nowMobile = window.innerWidth < 768;
      if (nowMobile === wasMobile.current) return;
      wasMobile.current = nowMobile;

      window.scrollTo({ top: 0, behavior: "smooth" });
      if (window.location.search || window.location.hash) {
        history.replaceState(null, "", window.location.pathname);
      }
    }

    window.addEventListener("resize", onResize, { passive: true });
    return () => window.removeEventListener("resize", onResize);
  }, []);
}