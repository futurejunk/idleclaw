import type { Metadata } from "next";
import { Bricolage_Grotesque, Manrope } from "next/font/google";
import "./globals.css";

const bricolage = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
});

const manrope = Manrope({
  variable: "--font-manrope",
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
    <html lang="en">
      <body
        className={`${bricolage.variable} ${manrope.variable} antialiased bg-background text-foreground`}
      >
        {children}
      </body>
    </html>
  );
}
