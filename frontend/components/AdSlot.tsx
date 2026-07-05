"use client";

import { useEffect, useRef } from "react";
import { ADSENSE_CLIENT_ID, IS_PLACEHOLDER } from "@/lib/adsense";

declare global {
  interface Window {
    adsbygoogle: unknown[];
  }
}

export default function AdSlot({ slot }: { slot?: string }) {
  const insRef = useRef<HTMLModElement>(null);

  useEffect(() => {
    if (IS_PLACEHOLDER) return;

    const el = insRef.current;
    // adsbygoogle throws "No slot size for availableWidth=0" if the <ins>
    // has no width yet (e.g. rendered inside a collapsed flex item). Only
    // push once the element actually has a nonzero width.
    if (!el || el.offsetWidth === 0) return;

    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // AdSense script not loaded yet — ignore.
    }
  }, []);

  // Dev / unconfigured: skip the real ad script entirely so it can't throw.
  if (IS_PLACEHOLDER) {
    return (
      <div className="flex w-full items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/40 py-8 text-xs text-slate-400">
        광고 영역 (AdSense 설정 후 표시)
      </div>
    );
  }

  // Loader script lives site-wide in layout.tsx; here we only render the unit.
  return (
    <ins
      ref={insRef}
      className="adsbygoogle"
      style={{ display: "block", width: "100%" }}
      data-ad-client={ADSENSE_CLIENT_ID}
      data-ad-slot={slot || "0000000000"}
      data-ad-format="auto"
      data-full-width-responsive="true"
    />
  );
}
