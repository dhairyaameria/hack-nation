import type { Metadata } from "next";
import { Newsreader, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

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
  title: "VC Brain — Maschmeyer Group",
  description: "Deploying $100K checks in 24 hours.",
};

// Runs before first paint so a dark-mode user never sees a flash of the
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
    <html
      lang="en"
      className={`${newsreader.variable} ${plexMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT }} />
      </head>
      <body className="min-h-full flex bg-background">
        <Sidebar />
        <main className="flex-1 min-w-0">{children}</main>
      </body>
    </html>
  );
}
