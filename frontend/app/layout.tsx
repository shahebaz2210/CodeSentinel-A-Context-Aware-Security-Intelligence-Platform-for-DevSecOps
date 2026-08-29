import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "CodeSentinel — Security Intelligence Platform",
  description:
    "Context-Aware Security Intelligence Platform for DevSecOps. AI-powered vulnerability detection, risk scoring, and remediation guidance.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-cs-bg text-cs-text`}>
        {children}
      </body>
    </html>
  );
}
