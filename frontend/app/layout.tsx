import type { Metadata } from "next";
import "./globals.css";

const TITLE = "너의 인생 책은? 5초 책 취향 테스트";
const DESCRIPTION = "5가지 질문에 답하고 지금 나에게 필요한 한국 책 한 권을 추천받아보세요.";

export const metadata: Metadata = {
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
