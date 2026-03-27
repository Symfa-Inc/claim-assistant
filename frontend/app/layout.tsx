import type { Metadata } from "next";

import "@/app/ui/global.css";
import { plusJakarta } from "@/app/ui/fonts";

export const metadata: Metadata = {
  title: "Claim Assistant",
  description: "AI-powered automation for insurance claim handling",
  metadataBase: new URL("https://claim-assistant.symfa.ai"),
  icons: {
    icon: [{ url: "/favicon.ico" }, { url: "/icon.png", type: "image/png" }],
    shortcut: "/favicon.ico",
    apple: "/icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${plusJakarta.variable} ${plusJakarta.className} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
