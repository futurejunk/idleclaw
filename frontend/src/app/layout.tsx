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
  metadataBase: new URL("https://idleclaw.com"),
  title: "IdleClaw — Free AI Chat Powered by Community GPUs",
  description:
    "Free AI chat powered by community GPU contributors. No accounts, no API keys — just open your browser and start chatting.",
  openGraph: {
    title: "IdleClaw — Free AI Chat Powered by Community GPUs",
    description:
      "Free AI chat powered by community GPU contributors. No accounts, no API keys — just open your browser and start chatting.",
    url: "https://idleclaw.com",
    type: "website",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-zinc-900 text-zinc-100`}
      >
        {children}
      </body>
    </html>
  );
}
