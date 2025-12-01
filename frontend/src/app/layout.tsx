import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Multi-Agent Market Research Platform",
  description: "AI-powered competitive intelligence using 7 specialized agents. Automated market research with real-time monitoring, SWOT analysis, and comprehensive reports.",
  keywords: ["AI", "multi-agent", "market research", "competitive intelligence", "LangGraph", "automation"],
  authors: [{ name: "Daniel Alexis Cruz" }],
  openGraph: {
    title: "Multi-Agent Market Research Platform",
    description: "7 AI agents working together for comprehensive competitive analysis",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
