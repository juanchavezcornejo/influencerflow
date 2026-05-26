import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InfluencerFlow",
  description: "Turn travel photos into Instagram posts — cost-conscious, non-destructive.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
