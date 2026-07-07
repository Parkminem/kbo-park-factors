import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "KBO Park Factors",
  description: "Daily KBO stadium and weather factors"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
