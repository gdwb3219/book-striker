import type { Metadata } from "next";
import Script from "next/script";
import { ADSENSE_CLIENT_ID, IS_PLACEHOLDER } from "@/lib/adsense";
import "./globals.css";

const TITLE = "유튜브 취향으로 찾는 내 인생 유튜버 & 책";
const DESCRIPTION =
  "9개 질문에 답하면 당신과 가장 잘 맞는 유튜버와, 그 팬들이 사랑하는 책 3권을 추천해드려요.";

// Production URL for absolute OG/twitter image links. Set NEXT_PUBLIC_SITE_URL
// in Vercel (e.g. https://book-striker.vercel.app); falls back to localhost.
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    images: ["/og-image.png"],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        {/* AdSense site-wide loader — required for site review + serving.
            Only injected once a real publisher id is configured. */}
        {!IS_PLACEHOLDER && (
          <Script
            id="adsbygoogle-init"
            async
            strategy="afterInteractive"
            crossOrigin="anonymous"
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADSENSE_CLIENT_ID}`}
          />
        )}
      </head>
      <body>{children}</body>
    </html>
  );
}
