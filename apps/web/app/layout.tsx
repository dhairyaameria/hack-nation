import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "Brain Venture — Deploy $100K checks in 24 hours",
  description:
    "Source exceptional founders before they raise. Screen with transparent trust. Decide with evidence-backed memos.",
};

// Runs beforeInteractive so a dark-mode user never sees a flash of the
// light theme. Falls back to the OS preference when nothing is stored.
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
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        {/* Non-blocking stylesheet — next/font/google was hanging SSR when
            fonts.googleapis.com was unreachable / slow on this network. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex bg-background">
        <Script id="theme-init" strategy="beforeInteractive">
          {THEME_INIT}
        </Script>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
