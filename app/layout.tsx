import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Korea Baseball Park Factors",
  description: "Daily Korea baseball stadium and weather factors"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
