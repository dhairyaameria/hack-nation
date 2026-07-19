import type { Metadata } from "next";
import { Newsreader, IBM_Plex_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Brain Venture — Deploy $100K checks in 24 hours",
  description:
    "Source exceptional founders before they raise. Screen with transparent trust. Decide with evidence-backed memos.",
};

// Runs beforeInteractive so a dark-mode user never sees a flash of the
// light theme. Falls back to the OS preference when nothing is stored.
// Use next/script (not a raw <script>) — React 19 / Next 16 warn on
// client-rendered script tags inside components.
const THEME_INIT = `
try {
  var t = localStorage.getItem('theme');
  if (t === 'dark' || (!t && matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
} catch (e) {}
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${newsreader.variable} ${plexMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex bg-background">
        <Script id="theme-init" strategy="beforeInteractive">
          {THEME_INIT}
        </Script>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
