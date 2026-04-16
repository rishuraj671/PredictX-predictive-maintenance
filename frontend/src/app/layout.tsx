import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
export const metadata: Metadata = {
  title: "PredictX — Predictive Maintenance Platform",
  description:
    "AI-powered predictive maintenance and RUL forecasting platform. Real-time anomaly detection, MILP-optimized scheduling.",
};
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-[#0a0e1a] text-slate-200`}>
        {children}
      </body>
    </html>
  );
}