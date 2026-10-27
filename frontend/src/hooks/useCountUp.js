import { useEffect, useRef, useState } from "react";

// Animated count-up for hero stats. Runs once when the component mounts
// (or when `target` ships its first real value). Respects
// prefers-reduced-motion by jumping straight to the final number.
export function useCountUp(target = 0, duration = 900) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduced || !target) {
      setValue(target);
      return;
    }

    const start = performance.now();
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1);
      // easeOutCubic for a natural deceleration feel
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return value;
}