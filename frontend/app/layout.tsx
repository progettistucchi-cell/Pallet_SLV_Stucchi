import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pallet Optimizer — SLV Stucchi",
  description: "Sistema di ottimizzazione palletizzazione per SLV Stucchi",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
