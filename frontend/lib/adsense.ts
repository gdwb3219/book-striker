// Single source of truth for AdSense config, read from env at build time.
// Set NEXT_PUBLIC_ADSENSE_CLIENT_ID in Vercel to the real "ca-pub-..." id.

export const ADSENSE_CLIENT_ID =
  process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID || "ca-pub-XXXXXXXXXXXXXXXX";

// True until a real publisher id is set — keeps ads (and ads.txt) inert in dev.
export const IS_PLACEHOLDER = ADSENSE_CLIENT_ID.includes("XXXX");

// ads.txt uses the "pub-..." form (no "ca-" prefix).
export const ADSENSE_PUB_ID = ADSENSE_CLIENT_ID.replace(/^ca-/, "");
