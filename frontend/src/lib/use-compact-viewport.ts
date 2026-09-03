import { useEffect, useState } from "react";

/**
 * True on phone-sized viewports.
 *
 * Used to mount a cheaper ambient background rather than to hide things after
 * the fact: the expensive work is the scroll listener and the animated blurred
 * layers, and neither stops costing anything just because it is invisible.
 */
export function useCompactViewport(query = "(max-width: 640px)"): boolean {
  const [compact, setCompact] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const media = window.matchMedia(query);
    const onChange = () => setCompact(media.matches);
    onChange();
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [query]);

  return compact;
}
