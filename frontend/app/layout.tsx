import type { Metadata } from "next";
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
      <body>{children}</body>
    </html>
  );
}
