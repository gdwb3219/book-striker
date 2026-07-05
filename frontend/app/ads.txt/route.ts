import { ADSENSE_PUB_ID, IS_PLACEHOLDER } from "@/lib/adsense";

// Served at /ads.txt. AdSense requires this file at the domain root to verify
// which sellers are authorized. Auto-generated from the configured publisher id.
export const dynamic = "force-static";

export function GET() {
  if (IS_PLACEHOLDER) {
    return new Response("", { status: 404 });
  }
  const body = `google.com, ${ADSENSE_PUB_ID}, DIRECT, f08c47fec0942fa0\n`;
  return new Response(body, {
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}
